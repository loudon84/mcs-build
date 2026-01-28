"""Settings and configuration for mcs-masterdata."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # App
    app_env: str = "dev"  # dev/staging/prod
    log_level: str = "INFO"

    # Database
    db_dsn: str = "postgresql://user:password@localhost:5432/mcs_masterdata"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    # API
    api_key: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls()

