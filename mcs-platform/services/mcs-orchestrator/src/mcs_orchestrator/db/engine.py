"""Database engine and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from mcs_orchestrator.settings import Settings


def create_db_engine(settings: Settings, async_mode: bool = False):
    """Create database engine."""
    if async_mode:
        return create_async_engine(
            settings.db_dsn,
            echo=settings.app_env == "dev",
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    else:
        return create_engine(
            settings.db_dsn,
            echo=settings.app_env == "dev",
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )


def create_session_factory(engine, async_mode: bool = False):
    """Create session factory."""
    if async_mode:
        return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    else:
        return sessionmaker(bind=engine, expire_on_commit=False)

