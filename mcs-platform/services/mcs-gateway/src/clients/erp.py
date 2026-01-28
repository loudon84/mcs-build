"""ERP system client."""

import httpx

from errors import (
    ERP_AUTH_FAILED,
    ERP_CONNECTION_FAILED,
    ERP_INVALID_RESPONSE,
    ERP_ORDER_CREATE_FAILED,
)
from settings import Settings


class ERPClient:
    """ERP system client."""

    def __init__(self, settings: Settings):
        """Initialize ERP client."""
        self.settings = settings
        self.base_url = settings.erp_base_url
        self.api_key = settings.erp_api_key
        self.tenant_id = settings.erp_tenant_id

    async def create_order(self, order_payload: dict) -> dict:
        """Create order in ERP system."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Content-Type": "application/json",
                }
                if self.api_key:
                    headers["X-API-Key"] = self.api_key
                if self.tenant_id:
                    headers["X-Tenant-ID"] = self.tenant_id

                response = await client.post(
                    f"{self.base_url}/api/orders",
                    json=order_payload,
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code == 401:
                    raise ValueError(f"{ERP_AUTH_FAILED}: Invalid credentials")

                response.raise_for_status()
                result = response.json()

                # Validate response structure
                if "sales_order_no" not in result:
                    raise ValueError(f"{ERP_INVALID_RESPONSE}: Missing sales_order_no in response")

                return {
                    "ok": True,
                    "sales_order_no": result.get("sales_order_no"),
                    "order_url": result.get("order_url", ""),
                    "order_id": result.get("order_id", ""),
                }

        except httpx.RequestError as e:
            raise ValueError(f"{ERP_CONNECTION_FAILED}: {str(e)}") from e
        except httpx.HTTPStatusError as e:
            raise ValueError(f"{ERP_ORDER_CREATE_FAILED}: HTTP {e.response.status_code}") from e
        except Exception as e:
            raise ValueError(f"{ERP_ORDER_CREATE_FAILED}: {str(e)}") from e

    async def get_order(self, order_id: str) -> dict:
        """Get order from ERP system."""
        try:
            async with httpx.AsyncClient() as client:
                headers = {}
                if self.api_key:
                    headers["X-API-Key"] = self.api_key
                if self.tenant_id:
                    headers["X-Tenant-ID"] = self.tenant_id

                response = await client.get(
                    f"{self.base_url}/api/orders/{order_id}",
                    headers=headers,
                    timeout=30.0,
                )

                response.raise_for_status()
                return response.json()

        except httpx.RequestError as e:
            raise ValueError(f"{ERP_CONNECTION_FAILED}: {str(e)}") from e
        except httpx.HTTPStatusError as e:
            raise ValueError(f"{ERP_ORDER_CREATE_FAILED}: HTTP {e.response.status_code}") from e
        except Exception as e:
            raise ValueError(f"{ERP_ORDER_CREATE_FAILED}: {str(e)}") from e

