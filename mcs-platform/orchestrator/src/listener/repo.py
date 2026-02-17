"""Data access layer for listener."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from listener.db.models import AttachmentFile, MessageRecord
from listener.utils import normalize_message_id


class ListenerRepo:
    """Repository for listener operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create_message_record(
        self,
        record_id: str,
        message_id: str,
        channel_type: str,
        provider: str,
        account: str,
        uid: str,
        from_email: str = "",
        received_at: Optional[str] = None,
    ) -> MessageRecord:
        """Create a new message record.
        
        from_email: message source (email From / wechat from_userid).
        received_at: ISO timestamp from channel; stored as datetime; None if missing/invalid.
        """
        received_dt: Optional[datetime] = None
        if received_at:
            try:
                received_dt = datetime.fromisoformat(received_at.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        canonical_id = normalize_message_id(message_id)
        record = MessageRecord(
            id=record_id,
            message_id=canonical_id,
            channel_type=channel_type,
            provider=provider,
            account=account,
            uid=uid,
            from_email=from_email or "",
            received_at=received_dt,
            processed=False,
        )
        self.session.add(record)
        self.session.commit()
        return record

    def find_message_by_id(self, message_id: str, channel_type: Optional[str] = None) -> Optional[MessageRecord]:
        """Find message record by message_id (raw or normalized; RFC 5322 allows angle brackets)."""
        canonical_id = normalize_message_id(message_id)
        stmt = select(MessageRecord).where(
            or_(
                MessageRecord.message_id == message_id,
                MessageRecord.message_id == canonical_id,
            )
        )
        if channel_type:
            stmt = stmt.where(MessageRecord.channel_type == channel_type)
        return self.session.scalar(stmt)

    def mark_as_processed(self, record_id: str) -> None:
        """Mark message record as processed."""
        record = self.session.get(MessageRecord, record_id)
        if record:
            record.processed = True
            record.processed_at = datetime.utcnow()
            self.session.commit()

    def get_attachment_file(self, file_id: UUID) -> Optional[AttachmentFile]:
        """Get attachment file record by id.

        Args:
            file_id: UUID of the attachment file record.

        Returns:
            AttachmentFile object, or None if not found.
        """
        return self.session.get(AttachmentFile, file_id)

    def create_attachment_file(
        self,
        file_id: UUID,
        message_id: str,
        file_path: str,
    ) -> AttachmentFile:
        """Create a new attachment file record.
        
        Args:
            file_id: UUID for the attachment file record.
            message_id: Email message ID.
            file_path: Relative file path (format: {message_id}/{filename}).
            
        Returns:
            AttachmentFile object.
        """
        record = AttachmentFile(
            id=file_id,
            message_id=message_id,
            file_path=file_path,
        )
        self.session.add(record)
        self.session.commit()
        return record
