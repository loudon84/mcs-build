"""API routes for mcs-email-listener."""

from fastapi import APIRouter, HTTPException, status

from mcs_email_listener.fetcher import parse_email_to_event, trigger_orchestrator
from mcs_email_listener.settings import Settings

router = APIRouter(prefix="/v1", tags=["email-listener"])


@router.post("/webhook/email")
async def webhook_email(
    email_data: dict,
    settings: Settings,
):
    """Receive email webhook (e.g., from Exchange)."""
    try:
        email_event = parse_email_to_event(
            email_data,
            provider="exchange",
            account=email_data.get("account", ""),
        )
        await trigger_orchestrator(email_event, settings)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process webhook: {str(e)}",
        ) from e


@router.post("/trigger/poll")
async def trigger_poll(settings: Settings):
    """Manually trigger email polling."""
    from mcs_email_listener.scheduler import EmailScheduler

    scheduler = EmailScheduler(settings)
    await scheduler._poll_emails()
    return {"status": "ok"}


@router.get("/status")
async def get_status():
    """Get service status."""
    return {"status": "ok", "service": "mcs-email-listener"}

