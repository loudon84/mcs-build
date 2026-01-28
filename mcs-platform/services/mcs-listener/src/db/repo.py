"""Data access layer for mcs-listener."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import MessageRecord


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
    ) -> MessageRecord:
        """Create a new message record."""
        record = MessageRecord(
            id=record_id,
            message_id=message_id,
            channel_type=channel_type,
            provider=provider,
            account=account,
            uid=uid,
            processed=False,
        )
        self.session.add(record)
        self.session.commit()
        return record

    def find_message_by_id(self, message_id: str, channel_type: Optional[str] = None) -> Optional[MessageRecord]:
        """Find message record by message_id."""
        stmt = select(MessageRecord).where(MessageRecord.message_id == message_id)
        if channel_type:
            stmt = stmt.where(MessageRecord.channel_type == channel_type)
        return self.session.scalar(stmt)

    def mark_as_processed(self, record_id: str) -> None:
        """Mark message record as processed."""
        from datetime import datetime

        record = self.session.get(MessageRecord, record_id)
        if record:
            record.processed = True
            record.processed_at = datetime.utcnow()
            self.session.commit()

