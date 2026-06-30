# backend/app/ml/live_inference.py
import asyncio
import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from app.ml.model_trainer import get_predictor
from app.ml.feature_engineering import FeatureEngineering
from app.data.data_processor import RaceDataProcessor
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class LiveRaceInference:
    """Handle real-time race prediction inference."""
    
    def __init__(self):
        self.predictor = get_predictor()
        self.data_processor = RaceDataProcessor()
        self.driver_history: Dict[int, List[Dict]] = {}
        self.last_inference_time = 0
        self.inference_count = 0
    
    def update_driver_history(self, driver_number: int, driver_data: Dict, max_history: int = 20) -> None:
        """
        Maintain rolling history of driver data for trend analysis.
        
        Args:
            driver_number: F1 driver number
            driver_data: Current driver data
            max_history: Maximum historical records to keep
        """
        if driver_number not in self.driver_history:
            self.driver_history[driver_number] = []
        
        self.driver_history[driver_number].append(driver_data.copy())
        
        # Keep only recent history
        if len(self.driver_history[driver_number]) > max_history:
            self.driver_history[driver_number] = self.driver_history[driver_number][-max_history:]
    
    async def predict_win_probabilities(
        self,
        drivers_data: List[Dict],
        track_status: Dict = None
    ) -> Dict[int, float]:
        """
        Calculate win probability for all drivers.
        Must complete in < 100ms for real-time dashboard updates.
        
        Args:
            drivers_data: List of current driver data
            track_status: Current track conditions
        
        Returns:
            Dictionary mapping driver_number to win_probability
        """
        start_time = time.time()
        
        try:
            # Update driver history
            for driver_data in drivers_data:
                self.update_driver_history(driver_data['driver_number'], driver_data)
            
            driver_numbers, probabilities = self._calculate_race_state_probabilities(drivers_data)

            if not driver_numbers:
                logger.warning("No valid driver state available for prediction")
                return {}

            # Create output dictionary
            result = {
                driver_numbers[i]: probabilities[i]
                for i in range(len(driver_numbers))
            }
            
            # Calculate inference metrics
            elapsed_ms = (time.time() - start_time) * 1000
            self.inference_count += 1
            self.last_inference_time = elapsed_ms
            
            # Warn if inference is slow
            if elapsed_ms > 100:
                logger.warning(f"Inference took {elapsed_ms:.2f}ms (> 100ms threshold)")
            else:
                logger.info(f"Inference completed in {elapsed_ms:.2f}ms")
            
            return result
        
        except Exception as e:
            logger.error(f"Error in win probability prediction: {str(e)}")
            return {}
    
    def _calculate_race_state_probabilities(self, drivers_data: List[Dict]) -> Tuple[List[int], np.ndarray]:
        """
        Score live win probability from real race state.

        The bundled LightGBM file is demo-trained on synthetic data, so live
        production scoring should prefer transparent race-state signals until a
        real historical model is trained and validated.
        """
        driver_numbers = []
        scores = []

        valid_positions = [
            float(driver.get('position') or 0)
            for driver in drivers_data
            if float(driver.get('position') or 0) > 0
        ]
        field_size = max(len(valid_positions), len(drivers_data), 20)

        for driver in drivers_data:
            driver_number = driver.get('driver_number')
            if driver_number is None:
                continue

            position = float(driver.get('position') or field_size)
            if position <= 0:
                position = field_size

            grid_position = float(driver.get('grid_position') or position)
            gap_to_leader = float(driver.get('gap_to_leader') or 0.0)
            last_lap = float(driver.get('last_lap_time') or 0.0)
            best_lap = float(driver.get('best_lap_time') or 0.0)
            avg_lap = float(driver.get('avg_lap_time') or 0.0)
            consistency = float(driver.get('lap_consistency') or 5.0)
            total_laps = float(driver.get('total_laps') or 0.0)
            tyre_age = float(driver.get('tyre_age') or 0.0)

            position_strength = (field_size - position + 1) / field_size
            grid_gain = (grid_position - position) / max(field_size, 1)
            race_progress = min(total_laps / 56.0, 1.0)

            pace_score = 0.0
            if best_lap > 0 and last_lap > 0:
                pace_score += np.clip((best_lap - last_lap) / best_lap, -0.08, 0.08) * 5
            if avg_lap > 0 and best_lap > 0:
                pace_score += np.clip((avg_lap - best_lap) / avg_lap, 0.0, 0.08) * 2

            gap_penalty = min(gap_to_leader / 90.0, 1.5)
            consistency_bonus = max(0.0, (5.0 - consistency) / 5.0)
            tyre_penalty = min(tyre_age / 80.0, 0.5)

            score = (
                3.2 * position_strength
                + 2.0 * race_progress * position_strength
                + 0.8 * grid_gain
                + pace_score
                + 0.4 * consistency_bonus
                - 1.2 * gap_penalty
                - 0.3 * tyre_penalty
            )

            driver_numbers.append(driver_number)
            scores.append(score)

        if not scores:
            return [], np.array([])

        return driver_numbers, self._softmax(np.array(scores, dtype=np.float32))

    def _softmax(self, scores: np.ndarray) -> np.ndarray:
        exp_scores = np.exp(scores - np.max(scores))
        return exp_scores / np.sum(exp_scores)

    def _normalize_probabilities(self, raw_probs: np.ndarray) -> np.ndarray:
        """
        Normalize raw model predictions to valid probabilities that sum to 1.
        
        Args:
            raw_probs: Raw model output scores
        
        Returns:
            Normalized probability array
        """
        # Ensure all values are positive
        probs = np.maximum(raw_probs, 0.001)
        
        # Apply softmax to convert to probabilities
        exp_probs = np.exp(probs - np.max(probs))  # For numerical stability
        normalized = exp_probs / np.sum(exp_probs)
        
        return normalized
    
    async def predict_top_finishers(
        self,
        drivers_data: List[Dict],
        top_n: int = 5
    ) -> List[Dict]:
        """
        Predict top N finishers and their probabilities.
        
        Args:
            drivers_data: List of driver data
            top_n: Number of top predictions to return
        
        Returns:
            List of driver predictions sorted by probability
        """
        try:
            win_probs = await self.predict_win_probabilities(drivers_data)
            
            # Create output list
            predictions = []
            for driver_data in drivers_data:
                driver_num = driver_data['driver_number']
                if driver_num in win_probs:
                    predictions.append({
                        'driver_number': driver_num,
                        'driver_name': driver_data.get('driver_name', 'Unknown'),
                        'team_name': driver_data.get('team_name', 'Unknown'),
                        'position': driver_data.get('position', 0),
                        'win_probability': float(win_probs[driver_num]),
                        'confidence': self._calculate_confidence(driver_data),
                        'trend': self._calculate_trend(driver_num),
                        'timestamp': datetime.utcnow().isoformat()
                    })
            
            # Sort by win probability
            predictions = sorted(predictions, key=lambda x: x['win_probability'], reverse=True)
            
            return predictions[:top_n]
        
        except Exception as e:
            logger.error(f"Error predicting top finishers: {str(e)}")
            return []
    
    def _calculate_confidence(self, driver_data: Dict) -> float:
        """
        Calculate confidence score for prediction.
        Based on data completeness and stability.
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence with more laps completed
        if driver_data.get('total_laps', 0) > 20:
            confidence += 0.2
        
        # Increase confidence with consistent lap times
        if driver_data.get('lap_consistency', 999) < 3.0:
            confidence += 0.2
        
        # Adjust based on position
        if driver_data.get('position', 20) <= 5:
            confidence += 0.1
        
        return float(np.clip(confidence, 0.0, 1.0))
    
    def _calculate_trend(self, driver_number: int) -> str:
        """
        Calculate trend direction for a driver.
        
        Returns:
            'UP', 'DOWN', or 'STABLE'
        """
        history = self.driver_history.get(driver_number, [])
        
        if len(history) < 3:
            return 'STABLE'
        
        # Compare last 3 positions
        positions = [h.get('position', 20) for h in history[-3:]]
        
        if positions[-1] < positions[0]:
            return 'UP'
        elif positions[-1] > positions[0]:
            return 'DOWN'
        else:
            return 'STABLE'
    
    def get_inference_stats(self) -> Dict:
        """Get inference performance statistics."""
        return {
            'last_inference_time_ms': self.last_inference_time,
            'total_inferences': self.inference_count,
            'status': 'ok' if self.last_inference_time < 100 else 'warning'
        }
    
    def reset(self) -> None:
        """Reset inference engine state."""
        self.driver_history.clear()
        self.last_inference_time = 0
        self.inference_count = 0
        logger.info("Inference engine reset")

# Global inference instance
_inference: Optional[LiveRaceInference] = None

async def get_live_inference() -> LiveRaceInference:
    """Get or create global live inference instance."""
    global _inference
    if _inference is None:
        _inference = LiveRaceInference()
    return _inference
