"""Settings and configuration for mcs-gateway."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # App
    app_env: str = "dev"
    log_level: str = "INFO"

    # ERP System
    erp_base_url: str = "http://localhost:9000"
    erp_api_key: str = ""
    erp_tenant_id: str = ""

    # Database
    db_dsn: str = "postgresql://user:password@localhost:5432/mcs_gateway"

    # Security
    api_key: str = ""
    jwt_public_key: str = ""
    allowed_tenants: list[str] = []

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls()

