"""API request/response schemas."""

from mcs_contracts import (
    EmailEvent,
    ManualReviewSubmitRequest,
    ManualReviewSubmitResponse,
    OrchestratorRunResult,
)

# Re-export contract models as API schemas
RunRequest = EmailEvent
RunResponse = OrchestratorRunResult
ManualReviewRequest = ManualReviewSubmitRequest
ManualReviewResponse = ManualReviewSubmitResponse


class ReplayRequest:
    """Replay request model."""

    message_id: str | None = None
    idempotency_key: str | None = None

