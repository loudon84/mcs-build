"""Settings and configuration for mcs-orchestrator."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # App
    app_env: str = "dev"  # dev/staging/prod
    log_level: str = "INFO"

    # Database
    db_dsn: str = "postgresql://user:password@localhost:5432/mcs_orchestrator"

    # Dify
    dify_base_url: str = "https://api.dify.ai"
    dify_contract_app_key: str = ""
    dify_order_app_key: str = ""

    # File Server
    file_server_base_url: str = "http://localhost:8001"
    file_server_api_key: str = ""

    # SMTP
    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""

    # LangSmith
    langsmith_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "mcs-platform"

    # Security
    api_key: str = ""
    jwt_public_key: str = ""
    allowed_tenants: list[str] = []

    # Master Data Service
    masterdata_api_url: str = "http://localhost:8002"
    masterdata_api_key: str = ""

    # Gateway
    gateway_url: str = "http://localhost:8003"

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls()

