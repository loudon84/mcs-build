"""Orchestrator API client."""

import httpx

from mcs_contracts import EmailEvent
from settings import Settings


async def trigger_orchestrator(email_event: EmailEvent, settings: Settings) -> None:
    """Trigger orchestrator API."""
    async with httpx.AsyncClient() as client:
        headers = {"X-API-Key": settings.orchestrator_api_key} if settings.orchestrator_api_key else {}
        response = await client.post(
            f"{settings.orchestrator_api_url}/v1/orchestrations/sales-email/run",
            json=email_event.model_dump(),
            headers=headers,
            timeout=30.0,
        )
        response.raise_for_status()

