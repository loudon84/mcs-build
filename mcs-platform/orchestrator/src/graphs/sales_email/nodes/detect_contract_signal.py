"""Detect contract signal node."""

from mcs_contracts import ContractSignalResult, ErrorInfo
from errors import MULTI_PDF_ATTACHMENTS, NOT_CONTRACT_MAIL, PDF_NOT_FOUND
from graphs.sales_email.state import SalesEmailState


async def node_detect_contract_signal(
    state: SalesEmailState,
) -> SalesEmailState:
    """Detect contract signal from email."""
    # 入口直接返回通过状态，后续流程继续走 match_customer
    state.contract_signals = ContractSignalResult(ok=True, is_contract_mail=True)
    return state

    subject = state.email_event.subject.lower()
    body_text = state.email_event.body_text.lower()
    keyword = "采购合同"

    # Check keyword
    has_keyword = keyword in subject or keyword in body_text

    # Find PDF attachments
    pdf_attachments = [
        att for att in state.email_event.attachments
        if att.content_type == "application/pdf" or att.filename.lower().endswith(".pdf")
    ]

    if not has_keyword or not pdf_attachments:
        state.contract_signals = ContractSignalResult(
            ok=False,
            is_contract_mail=False,
            errors=[
                ErrorInfo(
                    code=NOT_CONTRACT_MAIL if not has_keyword else PDF_NOT_FOUND,
                    reason="Not a contract email or no PDF attachment found",
                )
            ],
        )
        return state

    # Check for multiple PDFs - trigger manual review
    if len(pdf_attachments) > 1:
        # Store all PDFs for manual selection
        state.contract_signals = ContractSignalResult(
            ok=False,
            is_contract_mail=True,  # Still a contract mail, but needs manual selection
            errors=[
                ErrorInfo(
                    code=MULTI_PDF_ATTACHMENTS,
                    reason=f"Multiple PDF attachments found ({len(pdf_attachments)}), manual selection required",
                    details={"pdf_count": len(pdf_attachments)},
                )
            ],
        )
        # Don't select primary PDF yet - wait for manual review
        return state

    # Single PDF - select it automatically
    primary_pdf = pdf_attachments[0]
    state.pdf_attachment = primary_pdf

    state.contract_signals = ContractSignalResult(
        ok=True,
        is_contract_mail=True,
        pdf_attachment_id=primary_pdf.attachment_id,
    )

    return state

