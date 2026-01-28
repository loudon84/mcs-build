"""Resume functionality for manual review."""

import hashlib
from typing import Any

from mcs_contracts import ContactMatchResult, CustomerMatchResult, EmailAttachment, StatusEnum
from mcs_contracts.common import now_iso
from mcs_orchestrator.db.repo import OrchestratorRepo
from mcs_orchestrator.graphs.sales_email.state import SalesEmailState
from mcs_orchestrator.errors import OrchestratorError


# Allowed resume nodes (whitelist)
ALLOWED_RESUME_NODES = {
    "match_customer",
    "upload_pdf",
    "call_dify_contract",
    "call_dify_order_payload",
    "call_gateway",
}


def determine_resume_node(state: SalesEmailState, patch: dict[str, Any]) -> str:
    """Determine which node to resume from based on patch."""
    # If customer changed, resume from match_customer
    if "selected_customer_id" in patch and patch["selected_customer_id"]:
        return "match_customer"

    # If attachment changed, resume from upload_pdf
    if "selected_attachment_id" in patch and patch["selected_attachment_id"]:
        return "upload_pdf"

    # If customer/contact/contract changed, resume from call_dify_contract
    if "selected_customer_id" in patch or "selected_contact_id" in patch:
        return "call_dify_contract"

    # Default: resume from match_customer
    return "match_customer"


async def resume_from_node(
    state: SalesEmailState,
    resume_from_node: str,
    patch: dict[str, Any],
    repo: OrchestratorRepo,
    masterdata,
) -> SalesEmailState:
    """Resume graph execution from a specific node with state patch."""
    # Validate resume node
    if resume_from_node not in ALLOWED_RESUME_NODES:
        raise OrchestratorError(
            "INVALID_RESUME_NODE",
            f"Resume node {resume_from_node} is not in allowed list: {ALLOWED_RESUME_NODES}",
        )

    # Apply patch to state
    if "selected_customer_id" in patch and patch["selected_customer_id"]:
        customer = masterdata.get_customer_by_id(patch["selected_customer_id"]) if masterdata else None
        if customer:
            state.matched_customer = CustomerMatchResult(
                ok=True,
                customer_id=customer.customer_id,
                score=100.0,  # Manual selection = 100% confidence
                top_candidates=[],
            )

    if "selected_contact_id" in patch and patch["selected_contact_id"]:
        contact = masterdata.get_contact_by_email(state.email_event.from_email) if masterdata else None
        if not contact:
            # Try to find by contact_id
            for c in masterdata.contacts if masterdata else []:
                if c.contact_id == patch["selected_contact_id"]:
                    contact = c
                    break

        if contact:
            state.matched_contact = ContactMatchResult(
                ok=True,
                contact_id=contact.contact_id,
            )

    if "selected_attachment_id" in patch and patch["selected_attachment_id"]:
        # Find attachment by ID
        for att in state.email_event.attachments:
            if att.attachment_id == patch["selected_attachment_id"]:
                state.pdf_attachment = att
                break

    # Update manual_review decision
    if state.manual_review:
        state.manual_review["decision"] = {
            **state.manual_review.get("decision", {}),
            **patch,
            "decided_at": now_iso(),
        }

    # Recalculate idempotency_key if customer_id or file_sha256 changed
    if "selected_customer_id" in patch or "selected_attachment_id" in patch:
        message_id = state.email_event.message_id
        file_sha256 = state.pdf_attachment.sha256 if state.pdf_attachment and state.pdf_attachment.sha256 else ""
        customer_id = state.matched_customer.customer_id if state.matched_customer and state.matched_customer.ok else ""

        new_idempotency_key = hashlib.sha256(
            f"{message_id}:{file_sha256}:{customer_id}".encode()
        ).hexdigest()

        # Check if new idempotency_key hits SUCCESS
        record = repo.get_idempotency_record(new_idempotency_key)
        if record and record.status == StatusEnum.SUCCESS.value:
            # Short-circuit to notify_sales
            from mcs_contracts import ERPCreateOrderResult

            state.erp_result = ERPCreateOrderResult(
                ok=True,
                sales_order_no=record.sales_order_no,
                order_url=record.order_url,
            )
            state.final_status = StatusEnum.SUCCESS
            state.idempotency_key = new_idempotency_key
            return state

        state.idempotency_key = new_idempotency_key

    # Update status to RUNNING
    state.final_status = None  # Clear final status to allow continuation

    return state

