"""Dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from db.engine import create_db_engine, create_session_factory
from db.repo import OrchestratorRepo
from internal.db.engine import create_masterdata_engine, create_masterdata_session_factory
from internal.repo import MasterDataRepo
from settings import Settings
from services.gateway_service import GatewayService
from services.masterdata_service import MasterDataService
from tools.dify_client import DifyClient
from tools.file_server import FileServerClient
from tools.mailer import Mailer
from tools.masterdata_client import MasterDataClient


def get_settings() -> Settings:
    """Get application settings."""
    return Settings.from_env()


def get_db_session(settings: Annotated[Settings, Depends(get_settings)]) -> Session:
    """Get orchestration database session."""
    dsn = settings.get_orchestration_db_dsn()
    # Create engine with orchestration DSN
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(
        dsn,
        echo=settings.app_env == "dev",
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_masterdata_session(settings: Annotated[Settings, Depends(get_settings)]) -> Session:
    """Get masterdata database session."""
    engine = create_masterdata_engine(settings)
    session_factory = create_masterdata_session_factory(engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_repo(session: Annotated[Session, Depends(get_db_session)]) -> OrchestratorRepo:
    """Get repository instance."""
    return OrchestratorRepo(session)


def get_masterdata_client(settings: Annotated[Settings, Depends(get_settings)]) -> MasterDataClient:
    """Get master data client."""
    return MasterDataClient(settings.masterdata_api_url, settings.masterdata_api_key)


def get_file_server(settings: Annotated[Settings, Depends(get_settings)]) -> FileServerClient:
    """Get file server client."""
    return FileServerClient(settings.file_server_base_url, settings.file_server_api_key)


def get_dify_contract_client(settings: Annotated[Settings, Depends(get_settings)]) -> DifyClient:
    """Get Dify contract client."""
    return DifyClient(settings.dify_base_url, settings.dify_contract_app_key)


def get_dify_order_client(settings: Annotated[Settings, Depends(get_settings)]) -> DifyClient:
    """Get Dify order client."""
    return DifyClient(settings.dify_base_url, settings.dify_order_app_key)


def get_mailer(settings: Annotated[Settings, Depends(get_settings)]) -> Mailer:
    """Get mailer instance."""
    return Mailer(settings)


def get_gateway_service(settings: Annotated[Settings, Depends(get_settings)]) -> GatewayService:
    """Get gateway service."""
    return GatewayService(settings)


def get_masterdata_service(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_masterdata_session)],
) -> MasterDataService:
    """Get masterdata service."""
    repo = MasterDataRepo(session)
    return MasterDataService(repo, settings)


def get_listener_session(settings: Annotated[Settings, Depends(get_settings)]) -> Session:
    """Get listener database session."""
    from listener.db.engine import create_listener_engine, create_listener_session_factory
    
    engine = create_listener_engine(settings)
    session_factory = create_listener_session_factory(engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_listener_repo(
    session: Annotated[Session, Depends(get_listener_session)],
) -> "ListenerRepo":
    """Get listener repository."""
    from listener.repo import ListenerRepo

    return ListenerRepo(session)


def get_listener_service(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_listener_session)],
) -> "ListenerService":
    """Get listener service."""
    from listener.repo import ListenerRepo
    from services.listener_service import ListenerService
    
    # Note: OrchestrationService should be injected via app.state in main.py
    # For now, return service without orchestration_service (will be set later)
    repo = ListenerRepo(session)
    return ListenerService(settings, repo)


def get_orchestration_service(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_db_session)],
    repo: Annotated[OrchestratorRepo, Depends(get_repo)],
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
    file_server: Annotated[FileServerClient, Depends(get_file_server)],
    dify_contract_client: Annotated[DifyClient, Depends(get_dify_contract_client)],
    dify_order_client: Annotated[DifyClient, Depends(get_dify_order_client)],
    mailer: Annotated[Mailer, Depends(get_mailer)],
    gateway_service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> "OrchestrationService":
    """Get orchestration service."""
    from services.orchestration_service import OrchestrationService
    
    return OrchestrationService(
        settings=settings,
        repo=repo,
        masterdata_service=masterdata_service,
        file_server=file_server,
        dify_contract_client=dify_contract_client,
        dify_order_client=dify_order_client,
        mailer=mailer,
        gateway_service=gateway_service,
    )

