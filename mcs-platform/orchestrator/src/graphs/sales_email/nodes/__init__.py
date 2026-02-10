"""Sales email graph nodes."""

from graphs.sales_email.nodes.check_idempotency import node_check_idempotency as check_idempotency
from graphs.sales_email.nodes.load_masterdata import node_load_masterdata as load_masterdata
from graphs.sales_email.nodes.match_contact import node_match_contact as match_contact
from graphs.sales_email.nodes.detect_contract_signal import node_detect_contract_signal as detect_contract_signal
from graphs.sales_email.nodes.match_customer import node_match_customer as match_customer
from graphs.sales_email.nodes.upload_pdf import node_upload_pdf as upload_pdf
from graphs.sales_email.nodes.call_dify_contract import node_call_dify_contract as call_dify_contract
from graphs.sales_email.nodes.call_dify_order_payload import node_call_dify_order_payload as call_dify_order_payload
from graphs.sales_email.nodes.call_gateway import node_call_gateway as call_gateway
from graphs.sales_email.nodes.notify_sales import node_notify_sales as notify_sales
from graphs.sales_email.nodes.finalize import node_finalize as finalize

__all__ = [
    "check_idempotency",
    "load_masterdata",
    "match_contact",
    "detect_contract_signal",
    "match_customer",
    "upload_pdf",
    "call_dify_contract",
    "call_dify_order_payload",
    "call_gateway",
    "notify_sales",
    "finalize",
]
