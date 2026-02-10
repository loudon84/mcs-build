"""Redis checkpoint store for LangGraph."""

from typing import Optional

from langgraph.checkpoint.redis.aio import AsyncRedisSaver
import redis.asyncio as redis

from settings import Settings


class RedisCheckpointStore:
    """Redis checkpoint store implementation.
    
    使用 Redis 作为 LangGraph checkpoint 存储后端。
    优势：
    - 性能更好（内存存储）
    - 支持分布式部署
    - 无需数据库连接池管理
    - Windows 兼容性好（不依赖 psycopg）
    
    注意：
    - Redis 需要 RedisJSON 和 RediSearch 模块（Redis 8.0+ 内置）
    - 数据存储在内存中，需要配置持久化策略
    """

    def __init__(self, settings: Settings):
        """Initialize Redis checkpoint store."""
        self.settings = settings
        self.redis_url = settings.redis_url
        self.client: Optional[redis.Redis] = None
        self.checkpoint_saver: Optional[AsyncRedisSaver] = None

    async def initialize(self) -> None:
        """Initialize checkpoint store.
        
        RedisCheckpointStore 的作用：
        1. 为 LangGraph 提供状态持久化（checkpoint）
        2. 支持断点续跑（resume）：图执行中断后可以从上次状态恢复
        3. 支持人工审核后从指定节点恢复：人工审核通过后可以从特定节点重新执行
        
        初始化策略：
        - 创建 Redis 异步客户端
        - 创建 AsyncRedisSaver 实例
        - 无需表创建（Redis 自动管理）
        """
        from observability.logging import get_logger
        
        logger = get_logger()
        
        # 创建 Redis 异步客户端
        logger.info("Creating Redis async client", extra={"redis_url": self.redis_url.split("@")[-1] if "@" in self.redis_url else self.redis_url})
        
        try:
            # redis.asyncio.from_url 创建异步 Redis 客户端
            # decode_responses=True: 自动解码响应为字符串
            self.client = await redis.from_url(
                self.redis_url,
                decode_responses=True,
            )
            
            # 测试连接
            await self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(
                "Failed to create Redis connection",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "redis_url": self.redis_url.split("@")[-1] if "@" in self.redis_url else "***"
                }
            )
            raise
        
        # 创建 AsyncRedisSaver，使用 Redis 客户端
        try:
            logger.info("Initializing AsyncRedisSaver")
            # AsyncRedisSaver 接受 redis_client 参数（关键字参数）
            # 或者可以使用 redis_url 参数（字符串）
            # 我们直接传递客户端，避免重复创建连接
            self.checkpoint_saver = AsyncRedisSaver(redis_client=self.client)
            logger.info("Checkpoint store initialized successfully")
        except Exception as e:
            logger.error("Failed to setup checkpoint store", extra={"error": str(e), "error_type": type(e).__name__})
            if self.client:
                try:
                    await self.client.close()
                except Exception:
                    pass
                self.client = None
            raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self.client = None
        self.checkpoint_saver = None

    def get_checkpoint_saver_sync(self) -> AsyncRedisSaver:
        """Get checkpoint saver instance synchronously (must be initialized first)."""
        if self.checkpoint_saver is None:
            raise RuntimeError("Checkpoint store must be initialized before use. Call initialize() first.")
        return self.checkpoint_saver

    async def get_checkpoint_saver(self) -> AsyncRedisSaver:
        """Get checkpoint saver instance."""
        if self.checkpoint_saver is None:
            await self.initialize()
        assert self.checkpoint_saver is not None
        return self.checkpoint_saver

    async def cleanup_old_checkpoints(self, days_to_keep: int = 30) -> None:
        """Clean up old checkpoints (Redis TTL handles this automatically).
        
        注意：Redis checkpoint 使用 TTL 自动过期，通常不需要手动清理。
        如果需要手动清理，可以遍历所有 checkpoint key 并删除过期的。
        """
        # Redis checkpoint 使用 TTL 自动过期
        # 如果需要手动清理，可以实现遍历和删除逻辑
        pass
