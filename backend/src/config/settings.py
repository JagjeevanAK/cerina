"""Application settings using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    database_url: str = "postgresql+asyncpg://cerina:cerina_dev_password@localhost:5432/cerina"
    agents_database_url: str = "postgresql://cerina:cerina_dev_password@localhost:5432/cerina"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"    


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
