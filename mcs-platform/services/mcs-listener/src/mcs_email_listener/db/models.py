"""Database models for mcs-email-listener."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class EmailRecord(Base):
    """Email processing record."""

    __tablename__ = "email_records"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    message_id: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    account: Mapped[str] = mapped_column(String(200), nullable=False)
    uid: Mapped[str] = mapped_column(String(100), nullable=False)
    processed: Mapped[bool] = mapped_column(default=False, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_email_records_message_id", "message_id"),
    )

