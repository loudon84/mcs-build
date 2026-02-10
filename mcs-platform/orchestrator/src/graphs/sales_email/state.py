"""Sales email state definition."""

import operator
from typing import Annotated, Any, Optional

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


def _keep_first(
    left: Any, right: Any
) -> Any:
    """Reducer: keep first non-None value. Avoids InvalidUpdateError when input and node return both set the same key."""
    return left if left is not None else right


class SalesEmailState(BaseModel):
    """Sales email orchestration state.

    Single-value keys use Annotated[..., _keep_first] so LangGraph can merge
    initial state with node returns in the same step without InvalidUpdateError.
    """

    # Input
    email_event: Annotated[EmailEvent, _keep_first] = Field(
        ..., description="Input email event"
    )

    # Master data
    masterdata: Annotated[Optional[MasterData], _keep_first] = Field(
        None, description="Loaded master data"
    )

    # Matching results
    matched_contact: Annotated[Optional[ContactMatchResult], _keep_first] = Field(
        None, description="Matched contact result"
    )
    contract_signals: Annotated[Optional[ContractSignalResult], _keep_first] = Field(
        None, description="Contract signal detection result"
    )
    matched_customer: Annotated[Optional[CustomerMatchResult], _keep_first] = Field(
        None, description="Matched customer result"
    )

    # PDF processing
    pdf_attachment: Annotated[Optional[EmailAttachment], _keep_first] = Field(
        None, description="Selected PDF attachment"
    )
    file_upload: Annotated[Optional[FileUploadResult], _keep_first] = Field(
        None, description="File upload result"
    )

    # Dify results
    contract_result: Annotated[Optional[DifyContractResult], _keep_first] = Field(
        None, description="Dify contract recognition result"
    )
    order_payload_result: Annotated[
        Optional[DifyOrderPayloadResult], _keep_first
    ] = Field(None, description="Dify order payload result")

    # ERP result
    erp_result: Annotated[Optional[ERPCreateOrderResult], _keep_first] = Field(
        None, description="ERP order creation result"
    )

    # Idempotency
    idempotency_key: Annotated[Optional[str], _keep_first] = Field(
        None, description="Idempotency key"
    )

    # Final status
    final_status: Annotated[Optional[StatusEnum], _keep_first] = Field(
        None, description="Final orchestration status"
    )

    # Errors and warnings (append reducer so multiple nodes can add)
    errors: Annotated[list[ErrorInfo], operator.add] = Field(
        default_factory=list, description="Error list"
    )
    warnings: Annotated[list[str], operator.add] = Field(
        default_factory=list, description="Warning list"
    )

    # Timestamps & run identity (run_id 由调用方注入，finalize 用其更新 DB，不依赖 config)
    run_id: Annotated[Optional[str], _keep_first] = Field(
        None, description="Orchestration run_id (thread_id), used by finalize to update run status"
    )
    started_at: Annotated[Optional[str], _keep_first] = Field(
        None, description="Start timestamp"
    )
    finished_at: Annotated[Optional[str], _keep_first] = Field(
        None, description="Finish timestamp"
    )

    # Manual review
    manual_review: Annotated[Optional[dict[str, Any]], _keep_first] = Field(
        None, description="Manual review info"
    )

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

