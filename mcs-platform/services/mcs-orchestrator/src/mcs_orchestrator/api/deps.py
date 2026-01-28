"""Dependencies for FastAPI routes."""

from sqlalchemy.orm import Session

from mcs_orchestrator.db.engine import create_db_engine, create_session_factory
from mcs_orchestrator.db.repo import OrchestratorRepo
from mcs_orchestrator.settings import Settings
from mcs_orchestrator.tools.dify_client import DifyClient
from mcs_orchestrator.tools.file_server import FileServerClient
from mcs_orchestrator.tools.mailer import Mailer
from mcs_orchestrator.tools.masterdata_client import MasterDataClient


def get_settings() -> Settings:
    """Get application settings."""
    return Settings.from_env()


def get_db_session(settings: Settings) -> Session:
    """Get database session."""
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_repo(session: Session) -> OrchestratorRepo:
    """Get repository instance."""
    return OrchestratorRepo(session)


def get_masterdata_client(settings: Settings) -> MasterDataClient:
    """Get master data client."""
    return MasterDataClient(settings.masterdata_api_url, settings.masterdata_api_key)


def get_file_server(settings: Settings) -> FileServerClient:
    """Get file server client."""
    return FileServerClient(settings.file_server_base_url, settings.file_server_api_key)


def get_dify_contract_client(settings: Settings) -> DifyClient:
    """Get Dify contract client."""
    return DifyClient(settings.dify_base_url, settings.dify_contract_app_key)


def get_dify_order_client(settings: Settings) -> DifyClient:
    """Get Dify order client."""
    return DifyClient(settings.dify_base_url, settings.dify_order_app_key)


def get_mailer(settings: Settings) -> Mailer:
    """Get mailer instance."""
    return Mailer(settings)

