"""MCS Contracts - Shared data contracts for MCS Platform."""

from common import ErrorInfo, StatusEnum, now_iso
from email_event import EmailAttachment, EmailEvent
from masterdata import Company, Contact, Customer, MasterData, Product
from orchestrator import (
    ManualReviewCandidateContact,
    ManualReviewCandidateCustomer,
    ManualReviewCandidatePdf,
    ManualReviewCandidates,
    ManualReviewDecision,
    ManualReviewSubmitRequest,
    ManualReviewSubmitResponse,
    OrchestratorRunResult,
)
from results import (
    ContactMatchResult,
    ContractSignalResult,
    CustomerMatchResult,
    DifyContractResult,
    DifyOrderPayloadResult,
    ERPCreateOrderResult,
    FileUploadResult,
)

__version__ = "0.1.0"

__all__ = [
    # Common
    "StatusEnum",
    "ErrorInfo",
    "now_iso",
    # Email
    "EmailEvent",
    "EmailAttachment",
    # Master Data
    "MasterData",
    "Customer",
    "Contact",
    "Company",
    "Product",
    # Results
    "ContactMatchResult",
    "ContractSignalResult",
    "CustomerMatchResult",
    "FileUploadResult",
    "DifyContractResult",
    "DifyOrderPayloadResult",
    "ERPCreateOrderResult",
    # Orchestrator
    "OrchestratorRunResult",
    # Manual Review
    "ManualReviewCandidates",
    "ManualReviewCandidateCustomer",
    "ManualReviewCandidateContact",
    "ManualReviewCandidatePdf",
    "ManualReviewDecision",
    "ManualReviewSubmitRequest",
    "ManualReviewSubmitResponse",
]
