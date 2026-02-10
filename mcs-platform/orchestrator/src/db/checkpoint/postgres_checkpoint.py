"""PostgreSQL checkpoint store for LangGraph."""

import json
from typing import Any, AsyncIterator, Iterator, Optional
from uuid import UUID, uuid4

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from settings import Settings


class PostgresCheckpointStore:
    """PostgreSQL checkpoint store implementation.
    
    使用直接连接（不使用连接池），每次初始化时创建新连接。
    注意：这种方式在高并发场景下性能较差，建议使用连接池。
    """

    def __init__(self, settings: Settings):
        """Initialize PostgreSQL checkpoint store."""
        self.settings = settings
        dsn = settings.get_orchestration_db_dsn()
        # Ensure it's a standard postgresql:// URL (remove any SQLAlchemy driver prefixes)
        if dsn.startswith("postgresql+asyncpg://"):
            dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif dsn.startswith("postgresql+psycopg://"):
            dsn = dsn.replace("postgresql+psycopg://", "postgresql://", 1)
        self.conn_string = dsn
        self.conn: Optional[AsyncConnection] = None
        self.checkpoint_saver: Optional[AsyncPostgresSaver] = None

    async def initialize(self) -> None:
        """Initialize checkpoint tables.
        
        PostgresCheckpointStore 的作用：
        1. 为 LangGraph 提供状态持久化（checkpoint）
        2. 支持断点续跑（resume）：图执行中断后可以从上次状态恢复
        3. 支持人工审核后从指定节点恢复：人工审核通过后可以从特定节点重新执行
        
        初始化策略：
        - 创建直接连接（不使用连接池）
        - Windows 上确保使用 SelectorEventLoop（psycopg 要求）
        """
        import asyncio
        import sys
        
        # Windows 上强制设置事件循环策略（必须在创建连接之前）
        # psycopg 不支持 ProactorEventLoop，必须使用 SelectorEventLoop
        if sys.platform == "win32":
            # 设置事件循环策略（如果还没有设置）
            current_policy = asyncio.get_event_loop_policy()
            if not isinstance(current_policy, asyncio.WindowsSelectorEventLoopPolicy):
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
            # 检查当前运行的事件循环类型
            try:
                loop = asyncio.get_running_loop()
                if isinstance(loop, asyncio.ProactorEventLoop):
                    from observability.logging import get_logger
                    logger = get_logger()
                    logger.error(
                        "ProactorEventLoop detected on Windows. psycopg requires SelectorEventLoop. "
                        "Event loop policy was set but current loop is still ProactorEventLoop. "
                        "This indicates the event loop was created before policy was set."
                    )
                    raise RuntimeError(
                        "Cannot use ProactorEventLoop with psycopg. "
                        "Please ensure asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) "
                        "is called before creating any event loop."
                    )
            except RuntimeError:
                # 没有运行中的事件循环，这是正常的（在初始化时）
                pass
        
        from observability.logging import get_logger
        
        logger = get_logger()
        
        # 创建直接连接
        logger.info("Creating PostgreSQL direct connection", extra={"dsn": self.conn_string.split("@")[-1] if "@" in self.conn_string else "***"})
        
        try:
            self.conn = await AsyncConnection.connect(
                self.conn_string,
                autocommit=True,
                prepare_threshold=0,  # 禁用预编译语句缓存
                row_factory=dict_row,  # AsyncPostgresSaver 需要字典格式的行
            )
            logger.info("PostgreSQL connection established")
        except Exception as e:
            logger.error(
                "Failed to create PostgreSQL connection",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "conn_string": self.conn_string.split("@")[-1] if "@" in self.conn_string else "***"
                }
            )
            raise
        
        # 创建 AsyncPostgresSaver，使用直接连接
        try:
            logger.info("Initializing AsyncPostgresSaver (tables already exist)")
            self.checkpoint_saver = AsyncPostgresSaver(conn=self.conn)
            # await self.checkpoint_saver.setup()  # Commented out: tables already created
            logger.info("Checkpoint store initialized successfully")
        except Exception as e:
            logger.error("Failed to setup checkpoint store", extra={"error": str(e), "error_type": type(e).__name__})
            if self.conn:
                try:
                    await self.conn.close()
                except Exception:
                    pass
                self.conn = None
            raise

    async def close(self) -> None:
        """Close connection."""
        if self.conn:
            await self.conn.close()
            self.conn = None
        self.checkpoint_saver = None

    def get_checkpoint_saver_sync(self) -> AsyncPostgresSaver:
        """Get checkpoint saver instance synchronously (must be initialized first)."""
        if self.checkpoint_saver is None:
            raise RuntimeError("Checkpoint store must be initialized before use. Call initialize() first.")
        return self.checkpoint_saver

    async def get_checkpoint_saver(self) -> AsyncPostgresSaver:
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

