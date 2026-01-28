"""IMAP email listener."""

import imaplib
import email
from typing import Optional


class IMAPListener:
    """IMAP email listener."""

    def __init__(self, host: str, port: int, user: str, password: str):
        """Initialize IMAP listener."""
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.connection: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> None:
        """Connect to IMAP server."""
        try:
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            self.connection.login(self.user, self.password)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to IMAP server: {str(e)}") from e

    def poll_new_emails(self, folder: str = "INBOX") -> list[str]:
        """Poll for new emails."""
        if not self.connection:
            self.connect()

        self.connection.select(folder)
        _, message_numbers = self.connection.search(None, "UNSEEN")
        return message_numbers[0].split() if message_numbers[0] else []

    def fetch_email(self, uid: str) -> dict:
        """Fetch email content."""
        if not self.connection:
            self.connect()

        _, msg_data = self.connection.fetch(uid, "(RFC822)")
        email_body = msg_data[0][1]
        msg = email.message_from_bytes(email_body)

        return {
            "uid": uid,
            "message_id": msg.get("Message-ID"),
            "from": msg.get("From"),
            "to": msg.get("To"),
            "subject": msg.get("Subject"),
            "body": self._get_body(msg),
            "attachments": self._get_attachments(msg),
        }

    def mark_as_read(self, uid: str) -> None:
        """Mark email as read."""
        if not self.connection:
            return

        self.connection.store(uid, "+FLAGS", "\\Seen")

    def _get_body(self, msg: email.message.Message) -> str:
        """Extract email body."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
        return body

    def _get_attachments(self, msg: email.message.Message) -> list[dict]:
        """Extract email attachments."""
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    attachments.append({
                        "filename": part.get_filename(),
                        "content_type": part.get_content_type(),
                        "payload": part.get_payload(decode=True),
                    })
        return attachments

    def disconnect(self) -> None:
        """Disconnect from IMAP server."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except Exception:
                pass
            finally:
                self.connection = None

