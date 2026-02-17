"""Match contact node."""

from mcs_contracts import ContactMatchResult, ErrorInfo
from errors import CONTACT_NOT_FOUND
from graphs.sales_email.state import SalesEmailState


async def node_match_contact(
    state: SalesEmailState,
) -> SalesEmailState:
    """Match contact by email."""
    if not state.masterdata:
        state.add_error(
            "MASTERDATA_NOT_LOADED",
            "Master data not loaded",
        )
        return state

    from_email = state.email_event.from_email
    contact = state.masterdata.get_contact_by_email(from_email)

    if contact:
        state.matched_contact = ContactMatchResult(
            ok=True,
            contact_id=contact.contact_id,
            customer_id=contact.customer_id
        )
    else:
        state.matched_contact = ContactMatchResult(
            ok=False,
            errors=[
                ErrorInfo(
                    code=CONTACT_NOT_FOUND,
                    reason=f"Contact not found for email: {from_email}",
                )
            ],
        )

    return state

