"""Master data service client."""

import time
from typing import Optional

import httpx

from mcs_contracts import MasterData
from settings import Settings


class MasterDataClient:
    """Client for master data service."""

    def __init__(self, base_url: str, api_key: str, cache_ttl: int = 300):
        """Initialize master data client."""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self._cache: Optional[tuple[MasterData, int, float]] = None  # (data, version, expiry)

    def get_all(self) -> MasterData:
        """Get all master data (with caching)."""
        # Check cache
        if self._cache:
            data, version, expiry = self._cache
            if time.time() < expiry:
                # Check version
                current_version = self._get_version()
                if current_version == version:
                    return data
                # Version mismatch, clear cache
                self._cache = None

        # Cache miss or version mismatch, fetch from API
        with httpx.Client() as client:
            headers = {"X-API-Key": self.api_key} if self.api_key else {}
            response = client.get(f"{self.base_url}/v1/masterdata/all", headers=headers, timeout=30.0)
            response.raise_for_status()
            masterdata = MasterData(**response.json())

            # Update cache
            version = self._get_version()
            expiry = time.time() + self.cache_ttl
            self._cache = (masterdata, version, expiry)

            return masterdata

    def get_customer(self, customer_id: str):
        """Get customer by ID."""
        masterdata = self.get_all()
        return masterdata.get_customer_by_id(customer_id)

    def get_contact_by_email(self, email: str):
        """Get contact by email."""
        masterdata = self.get_all()
        return masterdata.get_contact_by_email(email)

    def _get_version(self) -> int:
        """Get current master data version."""
        with httpx.Client() as client:
            headers = {"X-API-Key": self.api_key} if self.api_key else {}
            response = client.get(f"{self.base_url}/v1/masterdata/version", headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()["version"]

