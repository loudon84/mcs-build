"""Listener API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_listener_service, get_settings
from services.listener_service import ListenerService
from settings import Settings

router = APIRouter(prefix="/v1/listener", tags=["listener"])


@router.post("/webhook/email")
async def webhook_email(
    email_data: dict,
    listener_service: Annotated[ListenerService, Depends(get_listener_service)],
):
    """Receive email webhook (e.g., from Exchange)."""
    try:
        await listener_service.handle_webhook_email(email_data)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        ) from e


@router.post("/webhook/wechat")
async def webhook_wechat(
    wechat_data: dict,
    listener_service: Annotated[ListenerService, Depends(get_listener_service)],
):
    """Receive WeChat webhook."""
    try:
        await listener_service.handle_webhook_wechat(wechat_data)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process WeChat webhook: {str(e)}",
        ) from e


@router.post("/trigger/poll")
async def trigger_poll(
    listener_service: Annotated[ListenerService, Depends(get_listener_service)],
):
    """Manually trigger polling for all enabled listeners."""
    try:
        await listener_service.trigger_poll()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger poll: {str(e)}",
        ) from e


@router.get("/status")
async def get_status(
    listener_service: Annotated[ListenerService, Depends(get_listener_service)],
):
    """Get service status."""
    return listener_service.get_status()
