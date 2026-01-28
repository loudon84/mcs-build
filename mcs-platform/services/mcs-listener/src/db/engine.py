"""Database engine and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import Settings


def create_db_engine(settings: Settings):
    """Create database engine."""
    return create_engine(settings.db_dsn, echo=settings.app_env == "dev")


def create_session_factory(engine):
    """Create session factory."""
    return sessionmaker(bind=engine)

