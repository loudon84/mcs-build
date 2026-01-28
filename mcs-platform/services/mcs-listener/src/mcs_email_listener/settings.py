"""Settings and configuration for mcs-email-listener."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # App
    app_env: str = "dev"
    log_level: str = "INFO"

    # Email Provider
    email_provider: str = "imap"  # imap/exchange/pop3

    # IMAP
    imap_host: str = "imap.example.com"
    imap_port: int = 993
    imap_user: str = ""
    imap_pass: str = ""

    # Exchange
    exchange_tenant_id: str = ""
    exchange_client_id: str = ""
    exchange_client_secret: str = ""

    # Polling
    poll_interval_seconds: int = 60

    # Orchestrator API
    orchestrator_api_url: str = "http://localhost:8000"
    orchestrator_api_key: str = ""

    # Database
    db_dsn: str = "postgresql://user:password@localhost:5432/mcs_email_listener"

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls()

