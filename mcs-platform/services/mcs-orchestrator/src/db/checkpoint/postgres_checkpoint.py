"""PostgreSQL checkpoint store for LangGraph."""

import json
from typing import Any, AsyncIterator, Iterator, Optional
from uuid import UUID, uuid4

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from settings import Settings


class PostgresCheckpointStore:
    """PostgreSQL checkpoint store implementation."""

    def __init__(self, settings: Settings):
        """Initialize PostgreSQL checkpoint store."""
        self.settings = settings
        self.engine = create_async_engine(
            settings.db_dsn.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.app_env == "dev",
        )
        self.checkpoint_saver: Optional[PostgresSaver] = None

    async def initialize(self) -> None:
        """Initialize checkpoint tables."""
        self.checkpoint_saver = PostgresSaver(self.engine)
        await self.checkpoint_saver.setup()

    async def get_checkpoint_saver(self) -> PostgresSaver:
        """Get checkpoint saver instance."""
        if self.checkpoint_saver is None:
            await self.initialize()
        assert self.checkpoint_saver is not None
        return self.checkpoint_saver

    async def cleanup_old_checkpoints(self, days_to_keep: int = 30) -> None:
        """Clean up checkpoints older than specified days."""
        # Implementation for cleanup logic
        # This would delete old checkpoint records
        pass

