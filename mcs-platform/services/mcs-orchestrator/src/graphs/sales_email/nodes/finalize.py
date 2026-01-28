"""Finalize node."""

from mcs_contracts import OrchestratorRunResult, StatusEnum, now_iso
from db.repo import OrchestratorRepo
from graphs.sales_email.nodes.generate_candidates import generate_manual_review_candidates
from graphs.sales_email.state import SalesEmailState
from observability.redaction import redact_dict


async def node_finalize(
    state: SalesEmailState,
    repo: OrchestratorRepo,
    run_id: str,
) -> SalesEmailState:
    """Finalize orchestration and create result."""
    # Determine final status and reason code
    reason_code = None
    if not state.final_status:
        if state.erp_result and state.erp_result.ok:
            state.final_status = StatusEnum.SUCCESS
        elif state.matched_contact and not state.matched_contact.ok:
            state.final_status = StatusEnum.UNKNOWN_CONTACT
            reason_code = "CONTACT_NOT_FOUND"
        elif state.contract_signals and not state.contract_signals.is_contract_mail:
            state.final_status = StatusEnum.IGNORED
        elif state.contract_result and not state.contract_result.ok:
            state.final_status = StatusEnum.CONTRACT_PARSE_FAILED
        elif state.order_payload_result and not state.order_payload_result.ok:
            state.final_status = StatusEnum.ORDER_PAYLOAD_BLOCKED
        elif state.erp_result and not state.erp_result.ok:
            state.final_status = StatusEnum.ERP_ORDER_FAILED
        else:
            state.final_status = StatusEnum.MANUAL_REVIEW
            # Determine reason code from errors
            if state.errors:
                reason_code = state.errors[0].code
            elif state.matched_customer and not state.matched_customer.ok and state.matched_customer.errors:
                reason_code = state.matched_customer.errors[0].code
            elif state.contract_signals and state.contract_signals.errors:
                reason_code = state.contract_signals.errors[0].code
            else:
                reason_code = "MANUAL_REVIEW"

    state.finished_at = now_iso()

    # Generate candidates if entering MANUAL_REVIEW
    if state.final_status == StatusEnum.MANUAL_REVIEW:
        candidates = generate_manual_review_candidates(state)
        state.set_manual_review(reason_code or "MANUAL_REVIEW", candidates=candidates)

        # Persist to state_json (redacted)
        state_dict = state.model_dump()
        redacted_state = redact_dict(state_dict)
    else:
        redacted_state = redact_dict(state.model_dump())

    # Update run status
    repo.update_run_status(
        run_id=run_id,
        status=state.final_status.value,
        finished_at=state.finished_at,
        state_json=redacted_state,
        errors_json=[e.model_dump() for e in state.errors],
        warnings_json=state.warnings,
    )

    return state

