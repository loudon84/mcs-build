"""Database engine and session management for masterdata."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import Settings


def create_masterdata_engine(settings: Settings):
    """Create masterdata database engine."""
    return create_engine(
        settings.masterdata_db_dsn,
        echo=settings.app_env == "dev",
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


def create_masterdata_session_factory(engine):
    """Create masterdata session factory."""
    return sessionmaker(bind=engine, expire_on_commit=False)
