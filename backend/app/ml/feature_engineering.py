# backend/app/ml/feature_engineering.py
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class FeatureEngineering:
    """Transform raw driver data into features for ML model."""
    
    # Feature scaling parameters (computed from historical data)
    FEATURE_STATS = {
        'position': {'mean': 10.5, 'std': 5.8},
        'grid_position': {'mean': 10.5, 'std': 5.8},
        'gap_to_leader': {'mean': 15.0, 'std': 20.0},
        'interval_to_ahead': {'mean': 1.2, 'std': 2.5},
        'last_lap_time': {'mean': 92.0, 'std': 5.0},
        'best_lap_time': {'mean': 88.0, 'std': 4.5},
        'avg_lap_time': {'mean': 90.5, 'std': 4.8},
        'lap_consistency': {'mean': 2.5, 'std': 1.5},
        'total_laps': {'mean': 35, 'std': 15},
        'tyre_age': {'mean': 12, 'std': 8},
        'stints_completed': {'mean': 2.5, 'std': 1.2}
    }
    
    @staticmethod
    def normalize_feature(value: float, feature_name: str) -> float:
        """Normalize feature using z-score normalization."""
        # Handle None/null values
        if value is None:
            value = 0.0
        
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = 0.0
        
        if feature_name not in FeatureEngineering.FEATURE_STATS:
            return float(value) / 100  # Default scaling
        
        stats = FeatureEngineering.FEATURE_STATS[feature_name]
        mean = stats['mean']
        std = stats['std']
        
        if std == 0:
            return 0.0
        
        normalized = (value - mean) / std
        return float(np.clip(normalized, -3, 3))  # Clip to prevent outliers
    
    @staticmethod
    def create_position_features(driver_data: Dict) -> Dict[str, float]:
        """Create features related to driver position."""
        position = float(driver_data.get('position') or 0)
        grid_position = float(driver_data.get('grid_position') or 0)
        gap_to_leader = float(driver_data.get('gap_to_leader') or 0.0)
        interval_to_ahead = float(driver_data.get('interval_to_ahead') or 0.0)
        
        return {
            'position_norm': FeatureEngineering.normalize_feature(position, 'position'),
            'grid_position_norm': FeatureEngineering.normalize_feature(grid_position, 'grid_position'),
            'position_gain': float(grid_position - position),
            'gap_to_leader_norm': FeatureEngineering.normalize_feature(gap_to_leader, 'gap_to_leader'),
            'interval_to_ahead_norm': FeatureEngineering.normalize_feature(interval_to_ahead, 'interval_to_ahead')
        }
    
    @staticmethod
    def create_pace_features(driver_data: Dict) -> Dict[str, float]:
        """Create features related to lap pace and performance."""
        last_lap = float(driver_data.get('last_lap_time') or 60.0)
        best_lap = float(driver_data.get('best_lap_time') or 60.0)
        avg_lap = float(driver_data.get('avg_lap_time') or 60.0)
        
        # Avoid division by zero and handle None values
        if best_lap == 0 or best_lap is None:
            best_lap = avg_lap if avg_lap > 0 else 60.0
        if avg_lap == 0 or avg_lap is None:
            avg_lap = last_lap if last_lap > 0 else 60.0
        if last_lap == 0 or last_lap is None:
            last_lap = best_lap if best_lap > 0 else 60.0
        
        # Ensure all values are valid floats
        last_lap = float(last_lap) if last_lap else 60.0
        best_lap = float(best_lap) if best_lap else 60.0
        avg_lap = float(avg_lap) if avg_lap else 60.0
        
        consistency = float(driver_data.get('lap_consistency') or 5.0)
        
        return {
            'last_lap_norm': FeatureEngineering.normalize_feature(last_lap, 'last_lap_time'),
            'best_lap_norm': FeatureEngineering.normalize_feature(best_lap, 'best_lap_time'),
            'avg_lap_norm': FeatureEngineering.normalize_feature(avg_lap, 'avg_lap_time'),
            'pace_trend': float((last_lap - best_lap) / best_lap) if best_lap > 0 else 0.0,
            'consistency_norm': FeatureEngineering.normalize_feature(consistency, 'lap_consistency'),
            'consistency_score': float(1.0 / (1.0 + consistency))  # Higher consistency = higher score
        }
    
    @staticmethod
    def create_tyre_features(driver_data: Dict) -> Dict[str, float]:
        """Create features related to tyre condition."""
        tyre_age = float(driver_data.get('tyre_age') or 0)
        tyre_compound = float(driver_data.get('tyre_compound') or 1)
        
        return {
            'tyre_age_norm': FeatureEngineering.normalize_feature(tyre_age, 'tyre_age'),
            'tyre_compound': tyre_compound,
            'tyre_degradation_factor': float(1.0 - min(tyre_age / 60, 1.0)),  # Assume 60 lap max
            'is_pit_eligible': float(tyre_age > 10)  # Typically after 10-15 laps
        }
    
    @staticmethod
    def create_stint_features(driver_data: Dict) -> Dict[str, float]:
        """Create features related to stints and strategy."""
        stints_completed = float(driver_data.get('stints_completed') or 0)
        total_laps = float(driver_data.get('total_laps') or 0)
        
        return {
            'stints_completed_norm': FeatureEngineering.normalize_feature(stints_completed, 'stints_completed'),
            'total_laps_norm': FeatureEngineering.normalize_feature(total_laps, 'total_laps'),
            'race_progress': float(total_laps / 56) if total_laps > 0 else 0.0,  # Normalized to typical race length
        }
    
    @staticmethod
    def create_momentum_features(current_data: Dict, historical_data: List[Dict]) -> Dict[str, float]:
        """Create features based on recent trend and momentum."""
        features = {
            'momentum_positive': 0.0,
            'position_improvement_rate': 0.0,
            'performance_trend': 0.0
        }
        
        if not historical_data or len(historical_data) < 2:
            return features
        
        try:
            # Sort by timestamp (most recent first)
            sorted_history = sorted(historical_data, key=lambda x: x.get('timestamp', ''), reverse=True)
            
            if len(sorted_history) >= 2:
                current_pos = float(current_data.get('position') or 0)
                prev_pos = float(sorted_history[0].get('position') or current_pos)
                
                # Positive momentum if position is improving
                features['momentum_positive'] = float(1.0 if prev_pos > current_pos else 0.0)
                features['position_improvement_rate'] = float(prev_pos - current_pos)
                
                # Performance trend based on pace
                current_pace = float(current_data.get('last_lap_time') or 60.0)
                prev_pace = float(sorted_history[0].get('last_lap_time') or current_pace)
                
                if prev_pace > 0 and current_pace > 0:
                    features['performance_trend'] = float((prev_pace - current_pace) / prev_pace)
        except Exception as e:
            logger.warning(f"Error creating momentum features: {str(e)}")
        
        return features
    
    @staticmethod
    def create_feature_vector(
        driver_data: Dict,
        historical_data: List[Dict] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Create complete feature vector for a single driver.
        
        Returns:
            Tuple of (feature_array, feature_names)
        """
        if historical_data is None:
            historical_data = []
        
        features = {}
        
        # Combine all feature groups
        features.update(FeatureEngineering.create_position_features(driver_data))
        features.update(FeatureEngineering.create_pace_features(driver_data))
        features.update(FeatureEngineering.create_tyre_features(driver_data))
        features.update(FeatureEngineering.create_stint_features(driver_data))
        features.update(FeatureEngineering.create_momentum_features(driver_data, historical_data))
        
        # Convert to ordered array
        feature_names = sorted(features.keys())
        feature_vector = np.array([features[name] for name in feature_names], dtype=np.float32)
        
        return feature_vector, feature_names
    
    @staticmethod
    def create_batch_features(
        drivers_data: List[Dict],
        historical_data_list: List[List[Dict]] = None
    ) -> Tuple[np.ndarray, List[str], List[int]]:
        """
        Create feature matrix for multiple drivers.
        
        Returns:
            Tuple of (feature_matrix, feature_names, driver_numbers)
        """
        if historical_data_list is None:
            historical_data_list = [[] for _ in drivers_data]
        
        feature_vectors = []
        driver_numbers = []
        feature_names = None
        
        for i, driver_data in enumerate(drivers_data):
            historical = historical_data_list[i] if i < len(historical_data_list) else []
            
            try:
                vector, names = FeatureEngineering.create_feature_vector(driver_data, historical)
                feature_vectors.append(vector)
                driver_numbers.append(driver_data['driver_number'])
                
                if feature_names is None:
                    feature_names = names
            except Exception as e:
                logger.warning(f"Error creating features for driver {driver_data.get('driver_number')}: {str(e)}")
                continue
        
        if not feature_vectors:
            return np.array([]), [], []
        
        feature_matrix = np.array(feature_vectors, dtype=np.float32)
        
        return feature_matrix, feature_names or [], driver_numbers
    
    @staticmethod
    def get_feature_names() -> List[str]:
        """Get standard feature names for the model."""
        dummy_driver = {
            'position': 1, 'grid_position': 1, 'gap_to_leader': 0, 'interval_to_ahead': 0,
            'last_lap_time': 88, 'best_lap_time': 88, 'avg_lap_time': 88, 'lap_consistency': 1,
            'total_laps': 20, 'tyre_compound': 1, 'tyre_age': 5, 'stints_completed': 1
        }
        _, names = FeatureEngineering.create_feature_vector(dummy_driver)
        return names