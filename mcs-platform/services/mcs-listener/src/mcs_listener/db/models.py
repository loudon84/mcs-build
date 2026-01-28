"""Database models for mcs-listener."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, String, Text
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
    processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_message_records_message_id", "message_id"),
        Index("ix_message_records_channel_type", "channel_type"),
        Index("ix_message_records_channel_message", "channel_type", "message_id"),
    )


# Backward compatibility alias
EmailRecord = MessageRecord

