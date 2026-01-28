"""Match customer node."""

from mcs_contracts import CustomerMatchResult
from mcs_orchestrator.errors import (
    CUSTOMER_CONTACT_MISMATCH,
    CUSTOMER_MATCH_LOW_SCORE,
    MULTI_CUSTOMER_AMBIGUOUS,
)
from mcs_orchestrator.graphs.sales_email.state import SalesEmailState
from mcs_orchestrator.settings import Settings
from mcs_orchestrator.tools.similarity import match_customer_by_filename, normalize_filename


async def node_match_customer(
    state: SalesEmailState,
    settings: Settings,
    similarity_threshold: float = 75.0,
) -> SalesEmailState:
    """Match customer by PDF filename."""
    if not state.masterdata or not state.pdf_attachment:
        return state

    filename = state.pdf_attachment.filename
    customers = state.masterdata.customers

    # Match by filename
    match_result = match_customer_by_filename(filename, customers, threshold=similarity_threshold)

    if not match_result.ok:
        state.matched_customer = match_result
        return state

    # Check for ambiguous candidates (multiple top candidates with close scores)
    if len(match_result.top_candidates) >= 2:
        top_score = match_result.top_candidates[0]["score"]
        second_score = match_result.top_candidates[1]["score"]
        score_diff = top_score - second_score

        # If scores are too close (difference < 5), trigger manual review
        if score_diff < 5.0:
            from mcs_contracts import ErrorInfo

            # Enhance top_candidates with evidence
            normalized_filename = normalize_filename(filename)
            enhanced_candidates = []
            for candidate in match_result.top_candidates:
                customer = state.masterdata.get_customer_by_id(candidate["customer_id"])
                if customer:
                    enhanced_candidates.append({
                        **candidate,
                        "evidence": {
                            "matched_tokens": [normalized_filename],
                            "filename_normalized": normalized_filename,
                        },
                    })
                else:
                    enhanced_candidates.append(candidate)

            state.matched_customer = CustomerMatchResult(
                ok=False,
                score=match_result.score,
                top_candidates=enhanced_candidates,
                errors=[
                    ErrorInfo(
                        code=MULTI_CUSTOMER_AMBIGUOUS,
                        reason=f"Multiple candidates with close scores (diff={score_diff:.1f}), manual selection required",
                        details={"top_score": top_score, "second_score": second_score, "diff": score_diff},
                    )
                ],
            )
            return state

    # Verify customer matches contact's customer_id
    if state.matched_contact and state.matched_contact.ok:
        matched_customer_id = match_result.customer_id
        contact_customer_id = state.masterdata.get_contact_by_email(
            state.email_event.from_email
        ).customer_id if state.masterdata.get_contact_by_email(state.email_event.from_email) else None

        if contact_customer_id and matched_customer_id != contact_customer_id:
            state.add_warning(
                f"Customer mismatch: matched {matched_customer_id} but contact belongs to {contact_customer_id}"
            )
            from mcs_contracts import ErrorInfo

            state.matched_customer = CustomerMatchResult(
                ok=False,
                score=match_result.score,
                top_candidates=match_result.top_candidates,
                errors=[
                    ErrorInfo(
                        code=CUSTOMER_CONTACT_MISMATCH,
                        reason="Matched customer does not match contact's customer",
                    )
                ],
            )
            return state

    state.matched_customer = match_result
    return state

