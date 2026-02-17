"""Match customer node."""

from mcs_contracts import CustomerMatchResult, ErrorInfo
from errors import CUSTOMER_MATCH_LOW_SCORE
from graphs.sales_email.state import SalesEmailState
from settings import Settings


async def node_match_customer(
    state: SalesEmailState,
    settings: Settings,
) -> SalesEmailState:
    """Match customer by matched_contact's customer_id from masterdata.customers."""
    if not state.masterdata or not state.matched_contact or not state.matched_contact.ok or not state.matched_contact.customer_id:
        return state

    customer_id = state.matched_contact.customer_id
    customer = state.masterdata.get_customer_by_id(customer_id)
    if not customer:
        state.matched_customer = CustomerMatchResult(
            ok=False,
            customer_id=None,
            score=0.0,
            errors=[
                ErrorInfo(
                    code=CUSTOMER_MATCH_LOW_SCORE,
                    reason="Customer not found in masterdata",
                    details={"customer_id": customer_id},
                )
            ],
        )
        return state

    state.matched_customer = CustomerMatchResult(
        ok=True,
        customer_id=customer_id,
        score=100.0,
    )
    return state

