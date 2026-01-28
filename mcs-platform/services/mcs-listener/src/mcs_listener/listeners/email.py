"""Email listener implementation."""

import email
import imaplib
from typing import Any, Optional

from mcs_listener.listeners.base import BaseListener


class EmailListener(BaseListener):
    """Email listener for IMAP/Exchange/POP3."""

    def __init__(
        self,
        provider: str = "imap",
        host: str = "",
        port: int = 993,
        user: str = "",
        password: str = "",
        exchange_tenant_id: str = "",
        exchange_client_id: str = "",
        exchange_client_secret: str = "",
    ):
        """Initialize email listener."""
        self.provider = provider
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.exchange_tenant_id = exchange_tenant_id
        self.exchange_client_id = exchange_client_id
        self.exchange_client_secret = exchange_client_secret
        self.connection: Optional[imaplib.IMAP4_SSL] = None

    @property
    def channel_type(self) -> str:
        """Return channel type."""
        return "email"

    async def connect(self) -> None:
        """Connect to email server."""
        if self.provider == "imap":
            try:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
                self.connection.login(self.user, self.password)
            except Exception as e:
                raise ConnectionError(f"Failed to connect to IMAP server: {str(e)}") from e
        elif self.provider == "exchange":
            # TODO: Implement Exchange connection
            raise NotImplementedError("Exchange provider not yet implemented")
        elif self.provider == "pop3":
            # TODO: Implement POP3 connection
            raise NotImplementedError("POP3 provider not yet implemented")
        else:
            raise ValueError(f"Unsupported email provider: {self.provider}")

    async def disconnect(self) -> None:
        """Disconnect from email server."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except Exception:
                pass
            finally:
                self.connection = None

    async def poll_new_messages(self, folder: str = "INBOX") -> list[str]:
        """Poll for new emails."""
        if not self.connection:
            await self.connect()

        if self.provider == "imap":
            self.connection.select(folder)
            _, message_numbers = self.connection.search(None, "UNSEEN")
            return message_numbers[0].split() if message_numbers[0] else []
        else:
            raise NotImplementedError(f"Polling not implemented for provider: {self.provider}")

    async def fetch_message(self, uid: str) -> dict[str, Any]:
        """Fetch email content."""
        if not self.connection:
            await self.connect()

        if self.provider == "imap":
            _, msg_data = self.connection.fetch(uid, "(RFC822)")
            email_body = msg_data[0][1]
            msg = email.message_from_bytes(email_body)

            return {
                "uid": uid,
                "message_id": msg.get("Message-ID", ""),
                "from": msg.get("From", ""),
                "to": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "body": self._get_body(msg),
                "attachments": self._get_attachments(msg),
                "provider": self.provider,
                "account": self.user,
            }
        else:
            raise NotImplementedError(f"Fetch not implemented for provider: {self.provider}")

    async def mark_as_processed(self, uid: str) -> None:
        """Mark email as read."""
        if not self.connection:
            return

        if self.provider == "imap":
            self.connection.store(uid, "+FLAGS", "\\Seen")
        else:
            raise NotImplementedError(f"Mark as processed not implemented for provider: {self.provider}")

    def _get_body(self, msg: email.message.Message) -> str:
        """Extract email body."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        return body

    def _get_attachments(self, msg: email.message.Message) -> list[dict[str, Any]]:
        """Extract email attachments."""
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": filename,
                            "content_type": part.get_content_type(),
                            "payload": part.get_payload(decode=True),
                        })
        return attachments

