# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        protected_namespaces=("settings_",)
    )

    # FastAPI Configuration
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    fastapi_debug: bool = True
    
    # OpenF1 API Configuration
    openf1_base_url: str = "https://api.openf1.org/v1"
    
    # Model Configuration
    model_update_interval: int = 3  # seconds
    prediction_interval: int = 5  # seconds
    inference_timeout: int = 100  # milliseconds
    
    # WebSocket Configuration
    ws_update_rate: int = 5  # seconds
    max_ws_connections: int = 100
    
    # Logging
    log_level: str = "INFO"
    
settings = Settings()
