"""Masterdata service for master data operations."""

from typing import Optional

from mcs_contracts import Company, Contact, Customer, MasterData, Product
from internal.cache.memory_cache import MemoryCache
from internal.cache.redis_cache import RedisCache
from internal.repo import MasterDataRepo
from settings import Settings


class MasterDataService:
    """Service for master data operations."""

    def __init__(self, repo: MasterDataRepo, settings: Optional[Settings] = None):
        """Initialize masterdata service."""
        self.repo = repo
        self.settings = settings
        # Initialize cache if Redis URL is provided
        if settings and settings.redis_url and settings.redis_url != "redis://localhost:6379/0":
            self.cache: Optional[RedisCache] = RedisCache(settings.redis_url, settings.cache_ttl_seconds)
        else:
            self.cache: Optional[MemoryCache] = MemoryCache(settings.cache_ttl_seconds if settings else 300)

    def get_all(self) -> MasterData:
        """Get all master data (with caching)."""
        try:
            version = self.repo.get_version()
        except Exception as e:
            # 如果获取版本失败，记录错误并尝试继续（使用版本0）
            from observability.logging import get_logger
            logger = get_logger()
            logger.warning(
                "Failed to get masterdata version, using version 0",
                extra={"error": str(e), "error_type": type(e).__name__}
            )
            version = 0

        # Try cache first
        if isinstance(self.cache, RedisCache):
            # Redis cache is async, but we're in sync context
            # For now, skip Redis cache in sync context, or make this method async
            # For simplicity, we'll use MemoryCache only in sync context
            cached_data = None
        else:
            cached_data = self.cache.get_all(version) if self.cache else None

        if cached_data:
            return cached_data

        # Cache miss, load from DB
        try:
            masterdata = self.repo.get_all_masterdata()
        except Exception as e:
            # 如果加载失败，记录详细错误并重新抛出
            from observability.logging import get_logger
            logger = get_logger()
            logger.error(
                "Failed to load masterdata from database",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "version": version
                },
                exc_info=True
            )
            raise

        # Update cache
        if isinstance(self.cache, MemoryCache):
            self.cache.set_all(masterdata, version)

        return masterdata

    def get_version(self) -> int:
        """Get current master data version."""
        return self.repo.get_version()

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID."""
        return self.repo.get_customer(customer_id)

    def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """Get contact by email."""
        return self.repo.get_contact_by_email(email)

    def get_company(self, company_id: str) -> Optional[Company]:
        """Get company by ID."""
        return self.repo.get_company(company_id)

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID."""
        return self.repo.get_product(product_id)

    def create_customer(self, customer: Customer) -> Customer:
        """Create a new customer."""
        self.repo.create_customer(customer)
        if isinstance(self.cache, MemoryCache):
            self.cache.invalidate()
        return customer

    def create_contact(self, contact: Contact) -> Contact:
        """Create a new contact."""
        self.repo.create_contact(contact)
        if isinstance(self.cache, MemoryCache):
            self.cache.invalidate()
        return contact

    def update_customer(self, customer: Customer) -> Customer:
        """Update an existing customer."""
        self.repo.update_customer(customer)
        if isinstance(self.cache, MemoryCache):
            self.cache.invalidate()
        return customer

    def update_contact(self, contact: Contact) -> Contact:
        """Update an existing contact."""
        self.repo.update_contact(contact)
        if isinstance(self.cache, MemoryCache):
            self.cache.invalidate()
        return contact

    def bulk_update(self, masterdata: MasterData) -> None:
        """Bulk update master data."""
        self.repo.bulk_update(masterdata)
        if isinstance(self.cache, MemoryCache):
            self.cache.invalidate()
