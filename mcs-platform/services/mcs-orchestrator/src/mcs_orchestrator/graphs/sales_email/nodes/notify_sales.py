"""Notify sales node."""

from mcs_contracts import StatusEnum
from mcs_contracts.common import now_iso
from mcs_orchestrator.graphs.sales_email.state import SalesEmailState
from mcs_orchestrator.tools.mailer import Mailer
from mcs_orchestrator.settings import Settings


async def node_notify_sales(
    state: SalesEmailState,
    mailer: Mailer,
    settings: Settings,
) -> SalesEmailState:
    """Notify sales via email (non-blocking)."""
    # Determine status and template
    if state.final_status:
        status = state.final_status
    elif state.erp_result and state.erp_result.ok:
        status = StatusEnum.SUCCESS
    elif state.contract_result and not state.contract_result.ok:
        status = StatusEnum.CONTRACT_PARSE_FAILED
    elif state.order_payload_result and not state.order_payload_result.ok:
        status = StatusEnum.ORDER_PAYLOAD_BLOCKED
    elif state.matched_contact and not state.matched_contact.ok:
        status = StatusEnum.UNKNOWN_CONTACT
    else:
        status = StatusEnum.MANUAL_REVIEW

    # Select template and render
    template_name = {
        StatusEnum.SUCCESS: "order_success.j2",
        StatusEnum.ERP_ORDER_FAILED: "order_failed.j2",
        StatusEnum.CONTRACT_PARSE_FAILED: "order_failed.j2",
        StatusEnum.MANUAL_REVIEW: "manual_review.j2",
        StatusEnum.UNKNOWN_CONTACT: "manual_review.j2",
    }.get(status, "order_failed.j2")

    # Prepare template context
    context = {
        "message_id": state.email_event.message_id,
        "errors": state.errors,
        "warnings": state.warnings,
        "reason": status.value,
    }

    if state.erp_result and state.erp_result.ok:
        context["sales_order_no"] = state.erp_result.sales_order_no
        context["order_url"] = state.erp_result.order_url
        customer = state.masterdata.get_customer_by_id(state.matched_customer.customer_id) if state.masterdata and state.matched_customer else None
        context["customer_name"] = customer.name if customer else "Unknown"

    # Render and send (non-blocking, failures are logged but don't affect state)
    try:
        body = mailer.render_template(template_name, **context)
        mailer.send_email(
            to=state.email_event.from_email,
            subject=f"订单处理结果 - {status.value}",
            body=body,
        )
    except Exception as e:
        # Log but don't fail
        state.add_warning(f"Failed to send notification email: {str(e)}")

    return state

