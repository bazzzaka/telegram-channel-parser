"""
Application configuration module.
"""

import os
from enum import Enum
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MapService(str, Enum):
    """Supported map services."""
    
    GOOGLE = "google"
    OSM = "osm"  # OpenStreetMap
    APPLE = "apple"


class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    APP_DEBUG: bool = Field(False, env="APP_DEBUG")
    APP_HOST: str = Field("0.0.0.0", env="APP_HOST")
    APP_PORT: int = Field(8000, env="APP_PORT")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    
    # Telegram API settings
    TG_API_ID: int = Field(..., env="TG_API_ID")
    TG_API_HASH: str = Field(..., env="TG_API_HASH")
    TG_PHONE: Optional[str] = Field(None, env="TG_PHONE")
    TG_PASSWORD: Optional[str] = Field(None, env="TG_PASSWORD")
    TG_BOT_TOKEN: Optional[str] = Field(None, env="TG_BOT_TOKEN")
    TG_CHANNELS: List[str] = Field([], env="TG_CHANNELS")

    # Database settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    
    # Map service configuration
    MAP_SERVICE: MapService = Field(MapService.GOOGLE, env="MAP_SERVICE")
    GOOGLE_MAPS_API_KEY: Optional[str] = Field(None, env="GOOGLE_MAPS_API_KEY")

    @property
    def tg_channels_list(self) -> List[str]:
        """Parse the TG_CHANNELS environment variable as a list."""
        if isinstance(self.TG_CHANNELS, list):
            return self.TG_CHANNELS
        return [c.strip() for c in self.TG_CHANNELS.split(",") if c.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Create settings instance
settings = Settings()