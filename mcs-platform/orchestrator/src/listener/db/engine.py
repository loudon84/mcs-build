"""Database engine and session management for listener."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from settings import Settings


def create_listener_engine(settings: Settings):
    """Create listener database engine."""
    return create_engine(
        settings.listener_db_dsn,
        echo=settings.app_env == "dev",
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


def create_listener_session_factory(engine):
    """Create listener session factory."""
    return sessionmaker(bind=engine, expire_on_commit=False)
