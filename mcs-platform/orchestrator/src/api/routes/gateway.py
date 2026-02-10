"""Gateway API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_gateway_service, get_settings
from services.gateway_service import GatewayService
from settings import Settings

router = APIRouter(prefix="/v1/orders", tags=["gateway"])


@router.post("")
async def create_order(
    order_payload: dict,
    gateway_service: Annotated[GatewayService, Depends(get_gateway_service)],
):
    """Create order in ERP system."""
    try:
        result = await gateway_service.create_order(order_payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}",
        ) from e


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    gateway_service: Annotated[GatewayService, Depends(get_gateway_service)],
):
    """Get order from ERP system."""
    try:
        result = await gateway_service.get_order(order_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get order: {str(e)}",
        ) from e
