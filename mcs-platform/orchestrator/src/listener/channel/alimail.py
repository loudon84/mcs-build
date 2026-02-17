"""Alimail email listener implementation."""

from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from listener.clients.alimail_client import AlimailClient
from listener.channel.base import BaseListener
from listener.repo import ListenerRepo
from observability.logging import get_logger
from tools.file_server import FileServerClient

logger = get_logger()


class AlimailListener(BaseListener):
    """Alimail email listener using REST API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        email_account: str,
        folder_id: str = "2",  # Default inbox
        base_url: str = "https://alimail-cn.aliyuncs.com",
        poll_size: int = 100,
        file_client: Optional[FileServerClient] = None,
        repo: Optional[ListenerRepo] = None,
        allow_from: Optional[list[str]] = None,
    ):
        """Initialize Alimail listener."""
        self.client = AlimailClient(client_id, client_secret, email_account, base_url)
        self.folder_id = folder_id
        self.poll_size = poll_size
        self._last_cursor: str = ""
        self.file_client = file_client
        self.repo = repo
        self.allow_from = allow_from or []

    @property
    def channel_type(self) -> str:
        """Return channel type."""
        return "email"

    def is_allowed(self, sender_id: str) -> bool:
        """Check if sender is allowed."""
        # If no allow list, allow all (backward compatible)
        if not self.allow_from:
            return True
        return sender_id in self.allow_from

    async def connect(self) -> None:
        """Connect (initialize OAuth and get token)."""
        await self.client.get_access_token()

    async def disconnect(self) -> None:
        """Disconnect (cleanup resources)."""
        await self.client.close()

    async def poll_new_messages(self, folder_id: str | None = None) -> list[str]:
        """Poll for new messages."""
        target_folder = folder_id or self.folder_id
        message_ids = []
        cursor = ""
        
        while True:
            response = await self.client.query_messages(
                folder_id=target_folder,
                is_read=False,
                cursor=cursor,
                size=self.poll_size,
                from_email='leon.zhao@smartcore-cloud.com'
            )
            
            messages = response.get("messages", [])
            for msg in messages:
                # Use 'id' as message_id (Alimail API returns 'id' field)
                message_ids.append(msg.get("id", ""))
            
            has_more = response.get("hasMore", False)
            cursor = response.get("nextCursor", "")
            
            if not has_more or not cursor:
                break
        
        return message_ids

    async def fetch_message(self, message_id: str) -> dict[str, Any]:
        """Fetch message content."""
        # Get message details
        message = await self.client.get_message(message_id)

        message = message['message'] if 'message' in message else message
        # Convert Alimail format to unified format
        from_email = ""
        if message.get("from"):
            from_obj = message["from"]
            if isinstance(from_obj, dict):
                from_email = from_obj.get("email", "")
            else:
                from_email = str(from_obj)
        
        # Convert recipients
        to_recipients = []
        for recipient in message.get("toRecipients", []):
            if isinstance(recipient, dict):
                to_recipients.append(recipient.get("email", ""))
            else:
                to_recipients.append(str(recipient))
        to_str = ",".join(to_recipients) if to_recipients else ""
        
        # Convert CC recipients
        cc_recipients = []
        for recipient in message.get("ccRecipients", []):
            if isinstance(recipient, dict):
                cc_recipients.append(recipient.get("email", ""))
            else:
                cc_recipients.append(str(recipient))
        cc_str = ",".join(cc_recipients) if cc_recipients else ""
        
        # Get body
        body_text = ""
        body_html = None
        if message.get("body"):
            body_obj = message["body"]
            body_text = body_obj.get("bodyText", "")
            body_html = body_obj.get("bodyHtml")
        
        # Handle timezone (Alimail returns UTC, need to convert to local time)
        received_at = message.get("receivedDateTime") or message.get("sentDateTime", "")
        if received_at:
            # Parse ISO 8601 format and convert from UTC to local time
            try:
                dt = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
                # Convert to local time (Beijing time is UTC+8)
                local_dt = dt.astimezone(timezone(timedelta(hours=8)))
                received_at = local_dt.isoformat()
            except (ValueError, AttributeError):
                # If parsing fails, use as-is
                pass
        
        # Get attachments if exists
        attachments = []
        if message.get("hasAttachments", False):
            attachment_list = await self.client.list_attachments(message_id)
            # Get message_id for file directory (use mailId if available, otherwise use message_id)
            file_message_id = message.get("mailId") or message_id
            
            for att in attachment_list:
                attachment_id = att.get("id", "")
                if attachment_id:
                    try:
                        # Download attachment
                        payload = await self.client.download_attachment(message_id, attachment_id)
                        
                        # Validate file stream
                        if not payload or len(payload) == 0:
                            # Skip empty attachments
                            continue
                        
                        filename = att.get("name", "")
                        content_type = att.get("contentType", "application/octet-stream")
                        
                        # Save file if file_client is available
                        file_id: Optional[UUID] = None
                        if self.file_client:
                            try:
                                # Save file to public/files/{message_id}/
                                base_dir = "public/files"
                                file_path = await self.file_client.save_file(
                                    file_bytes=payload,
                                    filename=filename,
                                    base_dir=base_dir,
                                    sub_dir=file_message_id,
                                )
                                
                                # Save to database if repo is available
                                if self.repo:
                                    file_id = uuid4()
                                    self.repo.create_attachment_file(
                                        file_id=file_id,
                                        message_id=file_message_id,
                                        file_path=file_path,
                                    )
                            except Exception as e:
                                logger.error(
                                    "Failed to save attachment",
                                    extra={
                                        "filename": filename,
                                        "message_id": file_message_id,
                                    },
                                    exc_info=True,
                                )
                        
                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "payload": payload,
                            "file_id": str(file_id) if file_id else None,
                        })
                    except Exception as e:
                        logger.error(
                            "Failed to download attachment",
                            extra={
                                "attachment_name": att.get("name", "unknown"),
                                "attachment_id": attachment_id,
                                "message_id": message_id,
                            },
                            exc_info=True,
                        )
        
        # Return unified format (same as EmailListener.fetch_message)
        return {
            "uid": message_id,  # Use message_id as uid
            "message_id": message.get("mailId") or message_id,  # Use mailId if available
            "from": from_email,
            "to": to_str,
            "cc": cc_str,
            "subject": message.get("subject", ""),
            "body": body_text,
            "body_html": body_html,  # Include HTML body for alimail
            "attachments": attachments,
            "provider": "alimail",
            "account": self.client.email_account,
            "received_at": received_at,
        }

    async def mark_as_processed(self, message_id: str) -> None:
        """Mark message as processed."""
        # Alimail API doesn't have a direct "mark as read" endpoint
        # This is handled by the scheduler through database records
        pass
