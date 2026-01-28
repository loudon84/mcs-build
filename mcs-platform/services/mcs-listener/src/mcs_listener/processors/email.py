"""Email message processor."""

import base64
import hashlib

from mcs_contracts import EmailAttachment, EmailEvent
from mcs_contracts.common import now_iso
from mcs_listener.processors.base import BaseProcessor


class EmailProcessor(BaseProcessor):
    """Email message processor."""

    @property
    def channel_type(self) -> str:
        """Return channel type."""
        return "email"

    def parse_to_event(self, message_data: dict) -> EmailEvent:
        """Parse email data to EmailEvent."""
        attachments = []
        for att_data in message_data.get("attachments", []):
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

        # Parse CC recipients (support both string and list formats)
        cc_list = []
        cc_data = message_data.get("cc", "")
        if cc_data:
            if isinstance(cc_data, str):
                cc_list = [email.strip() for email in cc_data.split(",") if email.strip()]
            elif isinstance(cc_data, list):
                cc_list = [str(email).strip() for email in cc_data if email]
        
        # Use received_at from message_data if available (for alimail), otherwise use now_iso()
        received_at = message_data.get("received_at") or now_iso()
        
        # Get body_html if available (for alimail)
        body_html = message_data.get("body_html")
        
        return EmailEvent(
            provider=message_data.get("provider", "imap"),
            account=message_data.get("account", ""),
            folder="INBOX",
            uid=message_data.get("uid", ""),
            message_id=message_data.get("message_id", ""),
            from_email=message_data.get("from", ""),
            to=message_data.get("to", "").split(",") if message_data.get("to") else [],
            cc=cc_list,
            subject=message_data.get("subject", ""),
            body_text=message_data.get("body", ""),
            body_html=body_html,
            received_at=received_at,
            attachments=attachments,
        )

