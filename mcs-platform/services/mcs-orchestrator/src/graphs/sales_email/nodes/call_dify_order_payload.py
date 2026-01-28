"""Call Dify order payload generation node."""

from mcs_contracts import DifyOrderPayloadResult
from errors import DIFY_ORDER_PAYLOAD_BLOCKED, OrchestratorError
from graphs.sales_email.state import SalesEmailState
from tools.dify_client import DifyClient


async def node_call_dify_order_payload(
    state: SalesEmailState,
    dify_client: DifyClient,
) -> SalesEmailState:
    """Call Dify order payload generation chatflow."""
    if not state.contract_result or not state.contract_result.ok:
        return state

    customer = state.masterdata.get_customer_by_id(state.matched_customer.customer_id) if state.masterdata and state.matched_customer else None
    contact = state.masterdata.get_contact_by_email(state.email_event.from_email) if state.masterdata else None

    if not customer or not contact:
        return state

    inputs = {
        "customer": customer.model_dump(),
        "contact": contact.model_dump(),
        "contract_meta": state.contract_result.contract_meta,
        "contract_items": state.contract_result.items,
        "file_url": state.file_upload.file_url if state.file_upload else "",
        "message_id": state.email_event.message_id,
    }

    result = await dify_client.chatflow_async(
        query="生成销售订单报�?,
        user=state.email_event.from_email,
        inputs=inputs,
    )

    payload_result = DifyOrderPayloadResult(**result)
    state.order_payload_result = payload_result

    if not payload_result.ok:
        state.add_error(
            DIFY_ORDER_PAYLOAD_BLOCKED,
            payload_result.errors[0].reason if payload_result.errors else "Dify order payload generation failed",
        )

    return state

