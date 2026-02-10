"""Call gateway node."""

from mcs_contracts import ERPCreateOrderResult, ErrorInfo, StatusEnum, now_iso
from errors import ERP_CREATE_FAILED
from graphs.sales_email.state import SalesEmailState
from observability.retry import retry_with_backoff
from services.gateway_service import GatewayService


@retry_with_backoff(max_retries=3)
async def node_call_gateway(
    state: SalesEmailState,
    gateway_service: GatewayService,
    repo,
) -> SalesEmailState:
    """Call gateway to create order."""
    if not state.order_payload_result or not state.order_payload_result.ok:
        return state

    # Call GatewayService (in-process, no HTTP)
    try:
        result_data = await gateway_service.create_order(state.order_payload_result.order_payload)

        erp_result = ERPCreateOrderResult(
            ok=True,
            sales_order_no=result_data.get("sales_order_no"),
            order_url=result_data.get("order_url"),
        )

        # Update idempotency record
        if state.idempotency_key:
            repo.upsert_idempotency_record(
                idempotency_key=state.idempotency_key,
                message_id=state.email_event.message_id,
                status=StatusEnum.SUCCESS,
                customer_id=state.matched_customer.customer_id if state.matched_customer else None,
                sales_order_no=erp_result.sales_order_no,
                order_url=erp_result.order_url,
            )

        state.erp_result = erp_result
    except Exception as e:
        state.erp_result = ERPCreateOrderResult(
            ok=False,
            errors=[
                ErrorInfo(
                    code=ERP_CREATE_FAILED,
                    reason=f"Gateway order creation failed: {str(e)}",
                )
            ],
        )
        state.add_error(ERP_CREATE_FAILED, f"Gateway order creation failed: {str(e)}")

    return state

