"""Gateway service for ERP integration."""

from gateway.erp_client import ERPClient
from settings import Settings


class GatewayService:
    """Service for gateway operations (ERP integration)."""

    def __init__(self, settings: Settings):
        """Initialize gateway service."""
        self.settings = settings
        self._erp_client = ERPClient(settings)

    async def create_order(self, order_payload: dict) -> dict:
        """Create order in ERP system."""
        return await self._erp_client.create_order(order_payload)

    async def get_order(self, order_id: str) -> dict:
        """Get order from ERP system."""
        return await self._erp_client.get_order(order_id)
