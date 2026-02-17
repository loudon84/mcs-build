"""Database models for listener."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class MessageRecord(Base):
    """Message processing record (unified for all channels)."""

    __tablename__ = "message_records"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    message_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # email, wechat, etc.
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # imap, exchange, wechat_work, etc.
    account: Mapped[str] = mapped_column(String(200), nullable=False)
    uid: Mapped[str] = mapped_column(String(100), nullable=False)
    from_email: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_message_records_message_id", "message_id"),
        Index("ix_message_records_channel_type", "channel_type"),
        Index("ix_message_records_channel_message", "channel_type", "message_id"),
    )


class AttachmentFile(Base):
    """Attachment file record."""

    __tablename__ = "attachment_files"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    message_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_attachment_files_message_id", "message_id"),
    )


# Backward compatibility alias
EmailRecord = MessageRecord
