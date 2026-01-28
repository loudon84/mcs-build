"""In-memory cache implementation for development."""

import time
from typing import Optional

from mcs_contracts import MasterData


class MemoryCache:
    """In-memory cache with TTL."""

    def __init__(self, ttl_seconds: int = 300):
        """Initialize memory cache."""
        self._cache: dict[str, tuple[MasterData, float]] = {}
        self._version_cache: dict[str, tuple[int, float]] = {}
        self.ttl_seconds = ttl_seconds

    def get_all(self, version: Optional[int] = None) -> Optional[MasterData]:
        """Get all master data from cache."""
        cache_key = "masterdata:all"
        if cache_key not in self._cache:
            return None

        data, expiry = self._cache[cache_key]
        if time.time() > expiry:
            del self._cache[cache_key]
            return None

        # Check version if provided
        if version is not None:
            version_key = "masterdata:version"
            if version_key in self._version_cache:
                cached_version, _ = self._version_cache[version_key]
                if cached_version != version:
                    # Version mismatch, invalidate cache
                    self.invalidate()
                    return None

        return data

    def set_all(self, masterdata: MasterData, version: int) -> None:
        """Set master data in cache."""
        cache_key = "masterdata:all"
        expiry = time.time() + self.ttl_seconds
        self._cache[cache_key] = (masterdata, expiry)

        version_key = "masterdata:version"
        self._version_cache[version_key] = (version, expiry)

    def invalidate(self) -> None:
        """Invalidate all cache."""
        self._cache.clear()
        self._version_cache.clear()

    def refresh(self, get_masterdata_func, get_version_func) -> MasterData:
        """Refresh cache from source."""
        version = get_version_func()
        masterdata = get_masterdata_func()
        self.set_all(masterdata, version)
        return masterdata

