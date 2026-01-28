"""Data access layer for mcs-orchestrator."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from mcs_contracts import ErrorInfo
from db.models import AuditEvent, IdempotencyRecord, OrchestrationRun
from errors import (
    RUN_NOT_IN_MANUAL_REVIEW,
    OrchestratorError,
)


class OrchestratorRepo:
    """Repository for orchestrator operations."""

    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session

    def create_run(
        self,
        run_id: str,
        message_id: str,
        status: str,
        started_at: datetime,
    ) -> OrchestrationRun:
        """Create a new orchestration run."""
        run = OrchestrationRun(
            run_id=run_id,
            message_id=message_id,
            status=status,
            started_at=started_at,
        )
        self.session.add(run)
        self.session.commit()
        return run

    def update_run_status(
        self,
        run_id: str,
        status: str,
        finished_at: Optional[datetime] = None,
        state_json: Optional[dict] = None,
        errors_json: Optional[list] = None,
        warnings_json: Optional[list] = None,
    ) -> OrchestrationRun:
        """Update orchestration run status."""
        run = self.session.get(OrchestrationRun, run_id)
        if not run:
            raise OrchestratorError("RUN_NOT_FOUND", f"Run {run_id} not found")

        run.status = status
        if finished_at:
            run.finished_at = finished_at
        if state_json is not None:
            run.state_json = state_json
        if errors_json is not None:
            run.errors_json = errors_json
        if warnings_json is not None:
            run.warnings_json = warnings_json

        self.session.commit()
        return run

    def write_audit_event(
        self,
        run_id: str,
        step: str,
        payload_json: dict,
    ) -> AuditEvent:
        """Write an audit event."""
        event = AuditEvent(
            id=uuid4(),
            run_id=run_id,
            step=step,
            payload_json=payload_json,
        )
        self.session.add(event)
        self.session.commit()
        return event

    def get_idempotency_record(self, idempotency_key: str) -> Optional[IdempotencyRecord]:
        """Get idempotency record by key."""
        return self.session.get(IdempotencyRecord, idempotency_key)

    def upsert_idempotency_record(
        self,
        idempotency_key: str,
        message_id: str,
        status: str,
        file_sha256: Optional[str] = None,
        customer_id: Optional[str] = None,
        sales_order_no: Optional[str] = None,
        order_url: Optional[str] = None,
    ) -> IdempotencyRecord:
        """Create or update idempotency record."""
        record = self.session.get(IdempotencyRecord, idempotency_key)
        if record:
            record.status = status
            record.sales_order_no = sales_order_no
            record.order_url = order_url
        else:
            record = IdempotencyRecord(
                idempotency_key=idempotency_key,
                message_id=message_id,
                file_sha256=file_sha256,
                customer_id=customer_id,
                status=status,
                sales_order_no=sales_order_no,
                order_url=order_url,
            )
            self.session.add(record)

        self.session.commit()
        return record

    def find_run_by_message_id(self, message_id: str) -> Optional[OrchestrationRun]:
        """Find orchestration run by message_id."""
        stmt = select(OrchestrationRun).where(OrchestrationRun.message_id == message_id).order_by(
            OrchestrationRun.started_at.desc()
        )
        return self.session.scalar(stmt)

    def get_run_with_state(self, run_id: str) -> Optional[OrchestrationRun]:
        """Get orchestration run with state_json."""
        return self.session.get(OrchestrationRun, run_id)

    def assert_run_in_status(self, run_id: str, expected_status: str) -> OrchestrationRun:
        """Assert run is in expected status, raise error if not."""
        run = self.session.get(OrchestrationRun, run_id)
        if not run:
            raise OrchestratorError("RUN_NOT_FOUND", f"Run {run_id} not found")

        if run.status != expected_status:
            raise OrchestratorError(
                RUN_NOT_IN_MANUAL_REVIEW,
                f"Run {run_id} is in status {run.status}, expected {expected_status}",
            )

        return run

    def write_manual_review_decision(
        self,
        run_id: str,
        decision_payload: dict,
    ) -> AuditEvent:
        """Write manual review decision to audit."""
        return self.write_audit_event(
            run_id=run_id,
            step="manual_review_submit",
            payload_json=decision_payload,
        )

