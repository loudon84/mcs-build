"""API routes for mcs-gateway."""

from fastapi import APIRouter, HTTPException, status

from clients.erp import ERPClient
from errors import ERP_ORDER_CREATE_FAILED
from settings import Settings

router = APIRouter(prefix="/v1", tags=["gateway"])


@router.post("/orders")
async def create_order(
    order_payload: dict,
    settings: Settings,
):
    """Create order in ERP system."""
    try:
        erp_client = ERPClient(settings)
        result = await erp_client.create_order(order_payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}",
        ) from e


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    settings: Settings,
):
    """Get order from ERP system."""
    try:
        erp_client = ERPClient(settings)
        result = await erp_client.get_order(order_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order: {str(e)}",
        ) from e

