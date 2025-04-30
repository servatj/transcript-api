from functools import lru_cache
from typing import Dict, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Transcript API"
    
    # Security
    API_KEY_NAME: str = "X-API-Key"
    API_KEY: str
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    RATE_LIMIT_MAX_REQUESTS: Dict[str, int] = {
        "youtube": 100,
        "tiktok": 50,
        "reels": 30
    }
    
    # OpenAI (for Whisper fallback)
    OPENAI_API_KEY: Optional[str] = None
    
    # Provider-specific settings
    TIKTOK_SESSION_ID: Optional[str] = None
    INSTAGRAM_USERNAME: Optional[str] = None
    INSTAGRAM_PASSWORD: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 