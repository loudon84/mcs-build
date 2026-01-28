"""Email fetching and processing."""

import base64
import hashlib
from typing import Any

import httpx

from mcs_contracts import EmailAttachment, EmailEvent, now_iso
from mcs_email_listener.settings import Settings


def parse_email_to_event(email_data: dict[str, Any], provider: str, account: str) -> EmailEvent:
    """Parse email data to EmailEvent."""
    attachments = []
    for att_data in email_data.get("attachments", []):
        payload = att_data.get("payload")
        sha256 = None
        bytes_b64 = None

        if payload:
            sha256 = hashlib.sha256(payload).hexdigest()
            bytes_b64 = base64.b64encode(payload).decode()

        attachments.append(
            EmailAttachment(
                attachment_id=att_data.get("filename", ""),
                filename=att_data.get("filename", ""),
                content_type=att_data.get("content_type", "application/octet-stream"),
                size=len(payload) if payload else 0,
                sha256=sha256,
                bytes_b64=bytes_b64,
            )
        )

    return EmailEvent(
        provider=provider,
        account=account,
        folder="INBOX",
        uid=email_data.get("uid", ""),
        message_id=email_data.get("message_id", ""),
        from_email=email_data.get("from", ""),
        to=email_data.get("to", "").split(",") if email_data.get("to") else [],
        cc=[],
        subject=email_data.get("subject", ""),
        body_text=email_data.get("body", ""),
        received_at=now_iso(),
        attachments=attachments,
    )


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

