"""Application settings using pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the path to the backend directory (where .env lives)
# Path: backend/src/agents/config/settings.py -> backend/
_BACKEND_DIR = Path(__file__).parent.parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://cerina:cerina_dev_password@localhost:5432/cerina"

    # LLM Provider
    llm_provider: Literal["anthropic", "openai", "openrouter"] = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    # Model names
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_model: str = "gpt-4o"
    openrouter_model: str = "anthropic/claude-sonnet-4-20250514"  # OpenRouter model format

    # OpenRouter settings
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = ""  # Optional: Your site URL for rankings
    openrouter_app_name: str = "Cerina CBT Agent"  # Your app name

    # LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "cerina-cbt-agents"

    # Application
    debug: bool = False
    log_level: str = "INFO"

    # Agent settings
    max_iterations: int = 5
    safety_threshold: float = 0.8
    empathy_threshold: float = 0.7


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
