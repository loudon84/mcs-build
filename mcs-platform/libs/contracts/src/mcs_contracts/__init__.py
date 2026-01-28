"""MCS Contracts - Shared data contracts for MCS Platform."""

from mcs_contracts.common import ErrorInfo, StatusEnum, now_iso
from mcs_contracts.email_event import EmailAttachment, EmailEvent
from mcs_contracts.masterdata import Company, Contact, Customer, MasterData, Product
from mcs_contracts.orchestrator import (
    ManualReviewCandidateContact,
    ManualReviewCandidateCustomer,
    ManualReviewCandidatePdf,
    ManualReviewCandidates,
    ManualReviewDecision,
    ManualReviewSubmitRequest,
    ManualReviewSubmitResponse,
    OrchestratorRunResult,
)
from mcs_contracts.results import (
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
