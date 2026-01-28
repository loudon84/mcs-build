"""MCS Contracts - Package entry point.

This module re-exports everything from the src package to allow
'from mcs_contracts import ...' imports to work.
"""

# Import everything from the src package modules
# Try absolute import first (when installed)
try:
    from src.common import ErrorInfo, StatusEnum, now_iso
    from src.email_event import EmailAttachment, EmailEvent
    from src.masterdata import Company, Contact, Customer, MasterData, Product
    from src.orchestrator import (
        ManualReviewCandidateContact,
        ManualReviewCandidateCustomer,
        ManualReviewCandidatePdf,
        ManualReviewCandidates,
        ManualReviewDecision,
        ManualReviewSubmitRequest,
        ManualReviewSubmitResponse,
        OrchestratorRunResult,
    )
    from src.results import (
        ContactMatchResult,
        ContractSignalResult,
        CustomerMatchResult,
        DifyContractResult,
        DifyOrderPayloadResult,
        ERPCreateOrderResult,
        FileUploadResult,
    )
except ImportError:
    # Fallback: direct import from same directory (development mode)
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
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
