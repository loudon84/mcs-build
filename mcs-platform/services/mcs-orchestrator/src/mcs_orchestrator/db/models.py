"""Database models for mcs-orchestrator."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class OrchestrationRun(Base):
    """Orchestration run record."""

    __tablename__ = "orchestration_runs"

    run_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    message_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    state_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    errors_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    warnings_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_orchestration_runs_message_id", "message_id"),
    )


class IdempotencyRecord(Base):
    """Idempotency record."""

    __tablename__ = "idempotency_records"

    idempotency_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    message_id: Mapped[str] = mapped_column(String(200), nullable=False)
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    sales_order_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AuditEvent(Base):
    """Audit event record."""

    __tablename__ = "audit_events"

    id: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    step: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_audit_events_run_id", "run_id"),
    )

