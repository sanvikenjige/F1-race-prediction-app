# backend/app/utils/helpers.py
import time
from typing import Any, Callable
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def measure_time(func: Callable) -> Callable:
    """Decorator to measure execution time of functions."""
    async def async_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"{func.__name__} executed in {elapsed_time:.2f}ms")
        return result
    
    def sync_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = (time.time() - start_time) * 1000
        logger.info(f"{func.__name__} executed in {elapsed_time:.2f}ms")
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

def validate_driver_data(driver_data: dict) -> bool:
    """Validate driver data structure."""
    required_fields = ['driver_id', 'position', 'grid_position', 'tyre_age', 'last_lap_time']
    return all(field in driver_data for field in required_fields)

def normalize_probability(prob: float) -> float:
    """Ensure probability is between 0 and 1."""
    return max(0.0, min(1.0, prob))

def format_timestamp(timestamp: int) -> str:
    """Format Unix timestamp to readable format."""
    from datetime import datetime
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

import asyncio