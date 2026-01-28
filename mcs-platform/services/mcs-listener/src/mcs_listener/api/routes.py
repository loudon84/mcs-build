"""API routes for mcs-listener."""

from fastapi import APIRouter, HTTPException, status

from mcs_listener.orchestrator_client import trigger_orchestrator
from mcs_listener.processors.email import EmailProcessor
from mcs_listener.processors.wechat import WeChatProcessor
from mcs_listener.settings import Settings

router = APIRouter(prefix="/v1", tags=["listener"])


@router.post("/webhook/email")
async def webhook_email(
    email_data: dict,
    settings: Settings,
):
    """Receive email webhook (e.g., from Exchange)."""
    try:
        processor = EmailProcessor()
        email_event = processor.parse_to_event(email_data)
        await trigger_orchestrator(email_event, settings)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        ) from e


@router.post("/webhook/wechat")
async def webhook_wechat(
    wechat_data: dict,
    settings: Settings,
):
    """Receive WeChat webhook."""
    try:
        processor = WeChatProcessor()
        email_event = processor.parse_to_event(wechat_data)
        await trigger_orchestrator(email_event, settings)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process WeChat webhook: {str(e)}",
        ) from e


@router.post("/trigger/poll")
async def trigger_poll(settings: Settings):
    """Manually trigger polling for all enabled listeners."""
    from mcs_listener.scheduler import UnifiedScheduler

    scheduler = UnifiedScheduler(settings)
    await scheduler.start()

    # Poll all channels
    if "email" in settings.get_enabled_listeners():
        await scheduler._poll_email()
    if "wechat" in settings.get_enabled_listeners():
        await scheduler._poll_wechat()

    await scheduler.stop()
    return {"status": "ok"}


@router.get("/status")
async def get_status(settings: Settings):
    """Get service status."""
    return {
        "status": "ok",
        "service": "mcs-listener",
        "enabled_channels": settings.get_enabled_listeners(),
    }

