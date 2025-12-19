"""Configuration settings for the MCP server."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MCP server configuration."""

    backend_url: str = "https://cerina.jagjeevan.me/api/v1"
    poll_interval: float = 2.0
    max_poll_attempts: int = 300  
    auto_approve: bool = True
    model_config = {
        "env_prefix": "CERINA_",
        "env_file": ".env",
        "extra": "ignore",
    }


settings = Settings()
