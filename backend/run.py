# backend/run.py
"""
F1 Race Prediction Service - Startup Script
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.utils.logger import setup_logger
from app.ml.model_trainer import get_predictor

logger = setup_logger(__name__)

async def initialize_system():
    """Initialize all system components."""
    logger.info("=" * 60)
    logger.info("🏁 F1 RACE WINNER PREDICTION SERVICE")
    logger.info("=" * 60)
    
    # Initialize model
    logger.info("\n📊 Initializing ML Model...")
    predictor = get_predictor()
    if predictor.is_trained:
        logger.info(f"✅ Model loaded successfully")
        logger.info(f"   - Training samples: {predictor.training_samples}")
        logger.info(f"   - Last trained: {predictor.last_training_time}")
    else:
        logger.warning("⚠️ Model not found, will initialize with synthetic data")
    
    # Configuration summary
    logger.info("\n⚙️ Configuration:")
    logger.info(f"   - Host: {settings.fastapi_host}")
    logger.info(f"   - Port: {settings.fastapi_port}")
    logger.info(f"   - OpenF1 API: {settings.openf1_base_url}")
    logger.info(f"   - Inference Timeout: {settings.inference_timeout}ms")
    logger.info(f"   - WebSocket Update Rate: {settings.ws_update_rate}s")
    
    logger.info("\n" + "=" * 60)
    logger.info("🚀 Starting FastAPI Server...")
    logger.info("=" * 60 + "\n")

def main():
    """Main entry point."""
    # Initialize system
    asyncio.run(initialize_system())
    
    # Start uvicorn server
    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.fastapi_debug,
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main()