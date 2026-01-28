"""Dependencies for FastAPI routes."""

from sqlalchemy.orm import Session

from cache.memory_cache import MemoryCache
from cache.redis_cache import RedisCache
from db.engine import create_db_engine, create_session_factory
from db.repo import MasterDataRepo
from settings import Settings


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


def get_cache(settings: Settings):
    """Get cache instance (Redis or Memory)."""
    if settings.redis_url and settings.redis_url != "redis://localhost:6379/0":
        return RedisCache(settings.redis_url, settings.cache_ttl_seconds)
    else:
        return MemoryCache(settings.cache_ttl_seconds)


def get_repo(session: Session) -> MasterDataRepo:
    """Get repository instance."""
    return MasterDataRepo(session)

