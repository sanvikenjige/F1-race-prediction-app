# backend/app/data/data_processor.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class RaceDataProcessor:
    """Process and clean raw F1 race data from OpenF1 API."""
    
    # Tyre compound mappings
    TYRE_COMPOUNDS = {
        'SOFT': 1,
        'MEDIUM': 2,
        'HARD': 3,
        'INTERMEDIATE': 4,
        'WET': 5
    }
    
    # Track status mappings
    TRACK_STATUS = {
        'GREEN': 0,
        'YELLOW': 1,
        'SAFETY_CAR': 2,
        'RED': 3
    }
    
    def __init__(self):
        self.driver_cache: Dict[int, Dict] = {}
        self.position_history: List[Dict] = []
    
    def process_intervals_data(self, intervals_data: List[Dict]) -> Dict[int, Dict]:
        """
        Process interval data to extract driver positions and gaps.
        
        Returns:
            Dict mapping driver_number to driver info with position and gap
        """
        if not intervals_data:
            return {}
        
        drivers = {}
        
        for interval in intervals_data:
            driver_num = interval.get('driver_number')
            gap_to_leader = interval.get('gap_to_leader')
            interval_to_pos_ahead = interval.get('interval_to_pos_ahead')
            
            if driver_num is not None:
                drivers[driver_num] = {
                    'driver_number': driver_num,
                    'gap_to_leader': gap_to_leader or 0.0,
                    'interval_to_ahead': interval_to_pos_ahead or 0.0,
                    'timestamp': interval.get('date')
                }
        
        return drivers

    def process_positions_data(self, positions_data: List[Dict]) -> Dict[int, Dict]:
        """
        Process running position data and keep the latest position per driver.
        """
        if not positions_data:
            return {}

        drivers = {}

        for position_record in positions_data:
            driver_num = position_record.get('driver_number')
            position = position_record.get('position')

            if driver_num is not None and position is not None:
                drivers[driver_num] = {
                    'driver_number': driver_num,
                    'position': position,
                    'timestamp': position_record.get('date')
                }

        return drivers
    
    def process_laps_data(self, laps_data: List[Dict]) -> Dict[int, Dict]:
        """
        Process lap data to extract lap times and performance metrics.
        
        Returns:
            Dict mapping driver_number to lap performance metrics
        """
        if not laps_data:
            return {}
        
        # Group by driver
        driver_laps = {}
        
        for lap in laps_data:
            driver_num = lap.get('driver_number')
            lap_duration = float(lap.get('lap_duration') or 0)

            if lap_duration <= 0:
                sector_1 = float(lap.get('duration_sector_1') or 0)
                sector_2 = float(lap.get('duration_sector_2') or 0)
                sector_3 = float(lap.get('duration_sector_3') or 0)
                lap_duration = sector_1 + sector_2 + sector_3
            
            if driver_num not in driver_laps:
                driver_laps[driver_num] = []
            
            driver_laps[driver_num].append({
                'lap_number': lap.get('lap_number'),
                'lap_duration': lap_duration,
                'sector_1': sector_1,
                'sector_2': sector_2,
                'sector_3': sector_3,
                'is_pit_lap': lap.get('pit_out_time') is not None
            })
        
        # Calculate metrics per driver
        driver_metrics = {}
        
        for driver_num, laps in driver_laps.items():
            # Filter out pit laps for lap time analysis
            race_laps = [lap for lap in laps if not lap['is_pit_lap'] and lap['lap_duration'] > 0]
            
            if race_laps:
                lap_times = [lap['lap_duration'] for lap in race_laps]
                driver_metrics[driver_num] = {
                    'driver_number': driver_num,
                    'last_lap_time': lap_times[-1],
                    'best_lap_time': min(lap_times),
                    'avg_lap_time': np.mean(lap_times),
                    'lap_consistency': np.std(lap_times),  # Lower is more consistent
                    'total_laps_completed': len(race_laps),
                    'latest_lap_number': max([lap['lap_number'] for lap in laps])
                }
        
        return driver_metrics
    
    def process_stints_data(self, stints_data: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Process stint data to extract tyre information.
        
        Returns:
            Dict mapping driver_number to list of stints with tyre info
        """
        if not stints_data:
            return {}
        
        driver_stints = {}
        
        for stint in stints_data:
            driver_num = stint.get('driver_number')
            compound = stint.get('compound', 'SOFT')
            lap_start = float(stint.get('lap_start') or 0)
            lap_end = float(stint.get('lap_end') or 0)
            
            if driver_num not in driver_stints:
                driver_stints[driver_num] = []
            
            driver_stints[driver_num].append({
                'compound': self.TYRE_COMPOUNDS.get(compound, 1),
                'compound_name': compound,
                'lap_start': lap_start,
                'lap_end': lap_end,
                'tyre_age': lap_end - lap_start if lap_end > 0 else 0,
                'stint_number': stint.get('stint_number', len(driver_stints[driver_num]) + 1)
            })
        
        return driver_stints
    
    def process_track_status(self, track_status_data: List[Dict]) -> Dict[str, Any]:
        """
        Process track status to get current conditions.
        
        Returns:
            Dict with current track status information
        """
        if not track_status_data:
            return {'status': 'UNKNOWN', 'code': -1}
        
        latest = track_status_data[-1] if track_status_data else {}
        status = latest.get('status', 'GREEN')
        
        return {
            'status': status,
            'code': self.TRACK_STATUS.get(status, 0),
            'message': latest.get('message', ''),
            'timestamp': latest.get('date')
        }
    
    def aggregate_driver_data(
        self,
        positions: Dict[int, Dict],
        intervals: Dict[int, Dict],
        laps: Dict[int, Dict],
        stints: Dict[int, List[Dict]],
        grid_positions: Dict[int, int],
        drivers_list: List[Dict]
    ) -> List[Dict]:
        """
        Aggregate all driver data into unified format for ML model.
        
        Returns:
            List of driver data dictionaries ready for model input
        """
        aggregated = []
        
        driver_numbers = set()
        driver_numbers.update(positions.keys())
        driver_numbers.update(intervals.keys())
        driver_numbers.update(laps.keys())
        driver_numbers.update(stints.keys())
        driver_numbers.update(d.get('driver_number') for d in drivers_list if d.get('driver_number') is not None)

        for driver_num in driver_numbers:
            try:
                driver_info = next(
                    (d for d in drivers_list if d.get('driver_number') == driver_num),
                    {'driver_number': driver_num}
                )
                
                position_data = positions.get(driver_num, {})
                interval_data = intervals.get(driver_num, {})
                lap_data = laps.get(driver_num, {})
                stints_data = stints.get(driver_num, [])
                
                # Get latest stint info
                latest_stint = stints_data[-1] if stints_data else {}
                
                # Ensure all numeric values are non-None floats
                def safe_float(val, default=0.0):
                    if val is None:
                        return default

                    if isinstance(val, str):
                        normalized = (
                            val.replace('+', '')
                            .replace('s', '')
                            .strip()
                        )

                        if not normalized or 'LAP' in normalized.upper():
                            return default

                        val = normalized

                    try:
                        return float(val)
                    except (TypeError, ValueError):
                        return default
                
                driver_record = {
                    'driver_number': driver_num,
                    'driver_name': driver_info.get('broadcast_name', 'Unknown'),
                    'team_name': driver_info.get('team_name', 'Unknown'),
                    'position': safe_float(position_data.get('position'), 0),
                    'grid_position': safe_float(grid_positions.get(driver_num), 0),
                    'gap_to_leader': safe_float(interval_data.get('gap_to_leader'), 0.0),
                    'interval_to_ahead': safe_float(interval_data.get('interval_to_ahead'), 0.0),
                    'last_lap_time': safe_float(lap_data.get('last_lap_time'), 60.0),
                    'best_lap_time': safe_float(lap_data.get('best_lap_time'), 60.0),
                    'avg_lap_time': safe_float(lap_data.get('avg_lap_time'), 60.0),
                    'lap_consistency': safe_float(lap_data.get('lap_consistency'), 5.0),
                    'total_laps': safe_float(lap_data.get('total_laps_completed'), 0),
                    'tyre_compound': safe_float(latest_stint.get('compound'), 1),
                    'tyre_age': safe_float(latest_stint.get('tyre_age'), 0),
                    'stints_completed': safe_float(len(stints_data), 0)
                }
                
                aggregated.append(driver_record)
            except Exception as e:
                logger.warning(f"Error aggregating data for driver {driver_num}: {str(e)}")
                continue
        
        return aggregated
    
    def validate_data_quality(self, driver_data: List[Dict]) -> Tuple[List[Dict], int]:
        """
        Validate and filter driver data for quality.
        
        Returns:
            Tuple of (cleaned_data, invalid_count)
        """
        valid_data = []
        invalid_count = 0
        
        for driver in driver_data:
            # Check for required fields
            if not all(k in driver for k in ['driver_number', 'position', 'grid_position']):
                invalid_count += 1
                continue
            
            # Check for NaN or invalid values
            if any(pd.isna(v) for v in driver.values() if isinstance(v, (int, float))):
                invalid_count += 1
                continue
            
            valid_data.append(driver)
        
        logger.info(f"Validated {len(valid_data)} drivers, {invalid_count} invalid records")
        return valid_data, invalid_count
