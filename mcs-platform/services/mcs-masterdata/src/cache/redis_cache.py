"""Redis cache implementation."""

import json
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from mcs_contracts import MasterData


class RedisCache:
    """Redis cache with version checking."""

    def __init__(self, redis_url: str, ttl_seconds: int = 300):
        """Initialize Redis cache."""
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self._client: Optional[Redis] = None

    async def _get_client(self) -> Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = await redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def get_all(self, version: Optional[int] = None) -> Optional[MasterData]:
        """Get all master data from cache."""
        client = await self._get_client()
        cache_key = "masterdata:all"

        # Check version first
        if version is not None:
            version_key = "masterdata:version"
            cached_version = await client.get(version_key)
            if cached_version and int(cached_version) != version:
                # Version mismatch, invalidate cache
                await self.invalidate()
                return None

        # Get cached data
        cached_data = await client.get(cache_key)
        if not cached_data:
            return None

        try:
            data_dict = json.loads(cached_data)
            return MasterData(**data_dict)
        except Exception:
            # Invalid cache data, clear it
            await self.invalidate()
            return None

    async def set_all(self, masterdata: MasterData, version: int) -> None:
        """Set master data in cache."""
        client = await self._get_client()
        cache_key = "masterdata:all"
        version_key = "masterdata:version"

        # Serialize masterdata
        data_json = json.dumps(masterdata.model_dump())

        # Set with TTL
        await client.setex(cache_key, self.ttl_seconds, data_json)
        await client.setex(version_key, self.ttl_seconds, str(version))

    async def invalidate(self) -> None:
        """Invalidate all cache."""
        client = await self._get_client()
        cache_key = "masterdata:all"
        version_key = "masterdata:version"
        await client.delete(cache_key, version_key)

    async def refresh(self, get_masterdata_func, get_version_func) -> MasterData:
        """Refresh cache from source."""
        version = get_version_func()
        masterdata = get_masterdata_func()
        await self.set_all(masterdata, version)
        return masterdata

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None

