"""Data access layer for mcs-email-listener."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from mcs_email_listener.db.models import EmailRecord


class EmailRecordRepo:
    """Repository for email records."""

    def __init__(self, session: Session):
        """Initialize repository."""
        self.session = session

    def get_by_message_id(self, message_id: str) -> EmailRecord | None:
        """Get email record by message_id."""
        stmt = select(EmailRecord).where(EmailRecord.message_id == message_id)
        return self.session.scalar(stmt)

    def create_record(self, record: EmailRecord) -> EmailRecord:
        """Create email record."""
        self.session.add(record)
        self.session.commit()
        return record

    def mark_processed(self, message_id: str) -> None:
        """Mark email as processed."""
        record = self.get_by_message_id(message_id)
        if record:
            record.processed = True
            from datetime import datetime
            record.processed_at = datetime.utcnow()
            self.session.commit()

