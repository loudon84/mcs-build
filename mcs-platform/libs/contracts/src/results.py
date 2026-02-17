"""Result models for orchestration steps."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from common import ErrorInfo


class ContactMatchResult(BaseModel):
    """Contact matching result."""

    ok: bool = Field(..., description="Whether matching succeeded")
    contact_id: Optional[str] = Field(None, description="Matched contact ID")
    customer_id: Optional[str] = Field(None, description="Matched contact's customer ID")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    errors: list[ErrorInfo] = Field(default_factory=list, description="Error information")


class ContractSignalResult(BaseModel):
    """Contract signal detection result."""

    ok: bool = Field(..., description="Whether contract signal detected")
    is_contract_mail: bool = Field(..., description="Whether email is contract-related")
    pdf_attachment_id: Optional[str] = Field(None, description="Selected PDF attachment ID")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    errors: list[ErrorInfo] = Field(default_factory=list, description="Error information")


class CustomerMatchResult(BaseModel):
    """Customer matching result."""

    ok: bool = Field(..., description="Whether matching succeeded")
    customer_id: Optional[str] = Field(None, description="Matched customer ID")
    score: float = Field(..., description="Match score", ge=0.0, le=100.0)
    top_candidates: list[dict[str, Any]] = Field(default_factory=list, description="Top candidate matches")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    errors: list[ErrorInfo] = Field(default_factory=list, description="Error information")


class FileUploadResult(BaseModel):
    """File upload result."""

    ok: bool = Field(..., description="Whether upload succeeded")
    file_url: Optional[str] = Field(None, description="Uploaded file URL")
    file_id: Optional[str] = Field(None, description="File identifier")
    sha256: Optional[str] = Field(None, description="File SHA256 hash")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    errors: list[ErrorInfo] = Field(default_factory=list, description="Error information")


class DifyContractResult(BaseModel):
    """Dify contract recognition result."""

    ok: bool = Field(..., description="Whether recognition succeeded")
    items: list[dict[str, Any]] = Field(default_factory=list, description="Recognized contract items")
    contract_meta: dict[str, Any] = Field(default_factory=dict, description="Contract metadata")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    errors: list[ErrorInfo] = Field(default_factory=list, description="Error information")
    raw_answer: Optional[str] = Field(None, description="Raw answer from Dify (if JSON parsing failed)")


class DifyOrderPayloadResult(BaseModel):
    """Dify order payload generation result."""

    ok: bool = Field(..., description="Whether generation succeeded")
    order_payload: dict[str, Any] = Field(default_factory=dict, description="Generated order payload")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    errors: list[ErrorInfo] = Field(default_factory=list, description="Error information")
    raw_answer: Optional[str] = Field(None, description="Raw answer from Dify (if JSON parsing failed)")


class ERPCreateOrderResult(BaseModel):
    """ERP order creation result."""

    ok: bool = Field(..., description="Whether order creation succeeded")
    sales_order_no: Optional[str] = Field(None, description="Sales order number")
    order_url: Optional[str] = Field(None, description="Order access URL")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    errors: list[ErrorInfo] = Field(default_factory=list, description="Error information")

