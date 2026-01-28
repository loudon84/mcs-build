"""Build sales email LangGraph."""

from langgraph.graph import END, START, StateGraph

from mcs_contracts import StatusEnum
from db.checkpoint.postgres_checkpoint import PostgresCheckpointStore
from db.repo import OrchestratorRepo
from graphs.sales_email.nodes import (
    call_dify_contract,
    call_dify_order_payload,
    call_gateway,
    check_idempotency,
    detect_contract_signal,
    finalize,
    load_masterdata,
    match_contact,
    match_customer,
    notify_sales,
    upload_pdf,
)
from graphs.sales_email.resume import determine_resume_node, resume_from_node
from graphs.sales_email.state import SalesEmailState
from settings import Settings
from tools.dify_client import DifyClient
from tools.file_server import FileServerClient
from tools.mailer import Mailer
from tools.masterdata_client import MasterDataClient


def build_sales_email_graph(
    settings: Settings,
    db_repo: OrchestratorRepo,
    checkpoint_store: PostgresCheckpointStore,
    masterdata_client: MasterDataClient,
    file_server: FileServerClient,
    dify_contract_client: DifyClient,
    dify_order_client: DifyClient,
    mailer: Mailer,
) -> StateGraph:
    """Build sales email LangGraph."""
    graph = StateGraph(SalesEmailState)

    # Add nodes
    graph.add_node("check_idempotency", lambda s: check_idempotency(s, db_repo))
    graph.add_node("load_masterdata", lambda s: load_masterdata(s, masterdata_client))
    graph.add_node("match_contact", match_contact)
    graph.add_node("detect_contract_signal", detect_contract_signal)
    graph.add_node("match_customer", lambda s: match_customer(s, settings))
    graph.add_node("upload_pdf", lambda s: upload_pdf(s, file_server, db_repo))
    graph.add_node("call_dify_contract", lambda s: call_dify_contract(s, dify_contract_client))
    graph.add_node("call_dify_order_payload", lambda s: call_dify_order_payload(s, dify_order_client))
    graph.add_node("call_gateway", lambda s: call_gateway(s, settings, db_repo))
    graph.add_node("notify_sales", lambda s: notify_sales(s, mailer, settings))
    graph.add_node("finalize", lambda s, run_id: finalize(s, db_repo, run_id))

    # Define edges
    graph.set_entry_point("check_idempotency")

    graph.add_edge("check_idempotency", "load_masterdata")
    graph.add_edge("load_masterdata", "match_contact")
    graph.add_edge("match_contact", "detect_contract_signal")
    graph.add_edge("detect_contract_signal", "match_customer")
    graph.add_edge("match_customer", "upload_pdf")
    graph.add_edge("upload_pdf", "call_dify_contract")
    graph.add_edge("call_dify_contract", "call_dify_order_payload")
    graph.add_edge("call_dify_order_payload", "call_gateway")
    graph.add_edge("call_gateway", "notify_sales")
    graph.add_edge("notify_sales", "finalize")
    graph.add_edge("finalize", END)

    # Conditional edges
    def should_skip_after_idempotency(state: SalesEmailState) -> str:
        """Check if should skip after idempotency check."""
        if state.final_status == StatusEnum.SUCCESS and state.erp_result and state.erp_result.ok:
            return "finalize"
        return "load_masterdata"

    graph.add_conditional_edges(
        "check_idempotency",
        should_skip_after_idempotency,
        {
            "finalize": "finalize",
            "load_masterdata": "load_masterdata",
        },
    )

    def should_continue_after_contact(state: SalesEmailState) -> str:
        """Check if should continue after contact matching."""
        if state.matched_contact and not state.matched_contact.ok:
            return "notify_sales"
        return "detect_contract_signal"

    graph.add_conditional_edges(
        "match_contact",
        should_continue_after_contact,
        {
            "notify_sales": "notify_sales",
            "detect_contract_signal": "detect_contract_signal",
        },
    )

    def should_continue_after_signal(state: SalesEmailState) -> str:
        """Check if should continue after contract signal detection."""
        if state.contract_signals and not state.contract_signals.is_contract_mail:
            return "finalize"
        return "match_customer"

    graph.add_conditional_edges(
        "detect_contract_signal",
        should_continue_after_signal,
        {
            "finalize": "finalize",
            "match_customer": "match_customer",
        },
    )

    # Compile with checkpoint
    checkpoint_saver = checkpoint_store.get_checkpoint_saver()
    return graph.compile(checkpointer=checkpoint_saver)

