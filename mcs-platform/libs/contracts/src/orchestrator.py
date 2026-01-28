"""Orchestrator result models."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from common import ErrorInfo, StatusEnum
from email_event import EmailAttachment
from masterdata import Contact, Customer


class ManualReviewCandidateCustomer(BaseModel):
    """Manual review candidate customer."""

    customer_id: str = Field(..., description="Customer ID")
    customer_num: str = Field(..., description="Customer number")
    customer_name: str = Field(..., description="Customer name")
    score: float = Field(..., description="Match score", ge=0.0, le=100.0)
    evidence: dict[str, Any] = Field(..., description="Match evidence (matched_tokens, filename_normalized)")
    suggested: bool = Field(False, description="Whether this is the suggested candidate")


class ManualReviewCandidateContact(BaseModel):
    """Manual review candidate contact."""

    contact_id: str = Field(..., description="Contact ID")
    name: str = Field(..., description="Contact name")
    email: str = Field(..., description="Contact email")
    telephone: Optional[str] = Field(None, description="Contact telephone")
    customer_id: str = Field(..., description="Associated customer ID")
    suggested: bool = Field(False, description="Whether this is the suggested candidate")


class ManualReviewCandidatePdf(BaseModel):
    """Manual review candidate PDF attachment."""

    attachment_id: str = Field(..., description="Attachment ID")
    filename: str = Field(..., description="Filename")
    sha256: Optional[str] = Field(None, description="SHA256 hash")
    size: int = Field(..., description="File size in bytes", ge=0)
    suggested: bool = Field(False, description="Whether this is the suggested candidate")


class ManualReviewCandidates(BaseModel):
    """Manual review candidates container."""

    pdfs: list[ManualReviewCandidatePdf] = Field(default_factory=list, description="PDF candidates")
    customers: list[ManualReviewCandidateCustomer] = Field(default_factory=list, description="Customer candidates")
    contacts: list[ManualReviewCandidateContact] = Field(default_factory=list, description="Contact candidates")


class ManualReviewDecision(BaseModel):
    """Manual review decision."""

    action: str = Field(..., description="Action: RESUME or BLOCK")
    selected_customer_id: Optional[str] = Field(None, description="Selected customer ID")
    selected_contact_id: Optional[str] = Field(None, description="Selected contact ID")
    selected_attachment_id: Optional[str] = Field(None, description="Selected attachment ID")
    override: dict[str, Any] = Field(default_factory=dict, description="Override fields (customer_num, po_number)")
    comment: Optional[str] = Field(None, description="Comment for BLOCK action")


class ManualReviewSubmitRequest(BaseModel):
    """Manual review submit request."""

    run_id: str = Field(..., description="Run ID")
    message_id: Optional[str] = Field(None, description="Message ID (for validation)")
    decision: ManualReviewDecision = Field(..., description="Decision")
    operator: dict[str, Any] = Field(..., description="Operator info (user_id, user_name, department)")
    auth: dict[str, Any] = Field(..., description="Auth info (tenant_id, scopes, request_id)")


class ManualReviewSubmitResponse(BaseModel):
    """Manual review submit response."""

    ok: bool = Field(..., description="Whether submission succeeded")
    status: Optional[str] = Field(None, description="Status: RESUMING or BLOCKED")
    resume: Optional[dict[str, Any]] = Field(None, description="Resume info (from_node, planned_path)")
    final_status: Optional[StatusEnum] = Field(None, description="Final status if BLOCKED")
    audit_id: Optional[str] = Field(None, description="Audit event ID")
    run_id: str = Field(..., description="Run ID")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    reason: Optional[str] = Field(None, description="Error reason if failed")


class OrchestratorRunResult(BaseModel):
    """Orchestrator run result."""

    run_id: str = Field(..., description="Run identifier")
    message_id: str = Field(..., description="Email message ID")
    status: StatusEnum = Field(..., description="Final status")
    started_at: str = Field(..., description="Start timestamp (ISO format)")
    finished_at: Optional[str] = Field(None, description="Finish timestamp (ISO format)")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")
    customer_id: Optional[str] = Field(None, description="Matched customer ID")
    contact_id: Optional[str] = Field(None, description="Matched contact ID")
    file_url: Optional[str] = Field(None, description="Uploaded file URL")
    sales_order_no: Optional[str] = Field(None, description="Sales order number")
    order_url: Optional[str] = Field(None, description="Order access URL")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    errors: list[ErrorInfo] = Field(default_factory=list, description="Error information")
    state_snapshot: Optional[dict[str, Any]] = Field(
        None, description="State snapshot for debugging (may be redacted in production)"
    )
    manual_review: Optional[dict[str, Any]] = Field(None, description="Manual review summary (if applicable)")

