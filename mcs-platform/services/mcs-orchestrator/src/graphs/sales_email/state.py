"""Sales email state definition."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from mcs_contracts import (
    ContactMatchResult,
    ContractSignalResult,
    CustomerMatchResult,
    DifyContractResult,
    DifyOrderPayloadResult,
    EmailAttachment,
    EmailEvent,
    ERPCreateOrderResult,
    ErrorInfo,
    FileUploadResult,
    ManualReviewCandidates,
    MasterData,
    StatusEnum,
)


class SalesEmailState(BaseModel):
    """Sales email orchestration state."""

    # Input
    email_event: EmailEvent = Field(..., description="Input email event")

    # Master data
    masterdata: Optional[MasterData] = Field(None, description="Loaded master data")

    # Matching results
    matched_contact: Optional[ContactMatchResult] = Field(None, description="Matched contact result")
    contract_signals: Optional[ContractSignalResult] = Field(None, description="Contract signal detection result")
    matched_customer: Optional[CustomerMatchResult] = Field(None, description="Matched customer result")

    # PDF processing
    pdf_attachment: Optional[EmailAttachment] = Field(None, description="Selected PDF attachment")
    file_upload: Optional[FileUploadResult] = Field(None, description="File upload result")

    # Dify results
    contract_result: Optional[DifyContractResult] = Field(None, description="Dify contract recognition result")
    order_payload_result: Optional[DifyOrderPayloadResult] = Field(None, description="Dify order payload result")

    # ERP result
    erp_result: Optional[ERPCreateOrderResult] = Field(None, description="ERP order creation result")

    # Idempotency
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")

    # Final status
    final_status: Optional[StatusEnum] = Field(None, description="Final orchestration status")

    # Errors and warnings
    errors: list[ErrorInfo] = Field(default_factory=list, description="Error list")
    warnings: list[str] = Field(default_factory=list, description="Warning list")

    # Timestamps
    started_at: Optional[str] = Field(None, description="Start timestamp")
    finished_at: Optional[str] = Field(None, description="Finish timestamp")

    # Manual review
    manual_review: Optional[dict[str, Any]] = Field(None, description="Manual review info")

    def add_error(self, code: str, reason: str, details: Optional[dict[str, Any]] = None) -> None:
        """Add an error to the state."""
        self.errors.append(ErrorInfo(code=code, reason=reason, details=details or {}))

    def add_warning(self, message: str) -> None:
        """Add a warning to the state."""
        self.warnings.append(message)

    def set_manual_review(
        self,
        reason_code: str,
        candidates: Optional[ManualReviewCandidates] = None,
        decision: Optional[dict[str, Any]] = None,
    ) -> None:
        """Set manual review information."""
        from mcs_contracts import now_iso

        self.manual_review = {
            "reason_code": reason_code,
            "created_at": now_iso(),
            "candidates": candidates.model_dump() if candidates else {},
            "decision": decision or {},
        }

