"""
TabWrap API Settings

Environment-based configuration using pydantic-settings.
All settings can be overridden via environment variables with TABWRAP_ prefix.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """TabWrap API configuration settings."""

    # Server configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS configuration
    cors_origins: list[str] = ["*"]

    # Logging
    log_level: str = "INFO"

    # Rate limiting
    rate_limit_per_minute: str = "10/minute"
    rate_limit_per_hour: str = "100/hour"

    class Config:
        env_prefix = "TABWRAP_"
        env_file = ".env"
        case_sensitive = False
