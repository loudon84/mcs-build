"""Build sales email LangGraph."""

from typing import Any

from langgraph.config import RunnableConfig
from langgraph.graph import END, START, StateGraph

from mcs_contracts import StatusEnum
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
from services.gateway_service import GatewayService
from services.masterdata_service import MasterDataService
from tools.dify_client import DifyClient
from tools.file_server import FileServerClient
from tools.mailer import Mailer


def build_sales_email_graph(
    settings: Settings,
    db_repo: OrchestratorRepo,
    checkpointer: Any,
    masterdata_service: MasterDataService,
    file_server: FileServerClient,
    dify_contract_client: DifyClient,
    dify_order_client: DifyClient,
    mailer: Mailer,
    gateway_service: GatewayService,
) -> StateGraph:
    """Build sales email LangGraph."""
    graph = StateGraph(SalesEmailState)

    # Add nodes
    # 注意：所有节点函数都是异步的，LangGraph 会自动处理异步函数
    # 使用包装函数来绑定额外参数，确保异步函数被正确调用
    
    # 为需要额外参数的节点创建包装函数
    async def check_idempotency_wrapper(state: SalesEmailState) -> SalesEmailState:
        """Wrapper for check_idempotency node."""
        return await check_idempotency(state, db_repo)
    
    async def load_masterdata_wrapper(state: SalesEmailState) -> SalesEmailState:
        """Wrapper for load_masterdata node."""
        return await load_masterdata(state, masterdata_service)
    
    async def match_customer_wrapper(state: SalesEmailState) -> SalesEmailState:
        """Wrapper for match_customer node."""
        return await match_customer(state, settings)
    
    async def upload_pdf_wrapper(state: SalesEmailState) -> SalesEmailState:
        """Wrapper for upload_pdf node."""
        return await upload_pdf(state, file_server, db_repo)
    
    async def call_dify_contract_wrapper(state: SalesEmailState) -> SalesEmailState:
        """Wrapper for call_dify_contract node."""
        return await call_dify_contract(state, dify_contract_client, settings)
    
    async def call_dify_order_payload_wrapper(state: SalesEmailState) -> SalesEmailState:
        """Wrapper for call_dify_order_payload node."""
        return await call_dify_order_payload(state, dify_order_client, settings)
    
    async def call_gateway_wrapper(state: SalesEmailState) -> SalesEmailState:
        """Wrapper for call_gateway node."""
        return await call_gateway(state, gateway_service, db_repo)
    
    async def notify_sales_wrapper(state: SalesEmailState) -> SalesEmailState:
        """Wrapper for notify_sales node."""
        return await notify_sales(state, mailer, settings)
    
    # 为 finalize 节点创建包装函数，从 config 中获取 run_id (thread_id)
    # LangGraph 节点函数可以接受 (state, config) 参数，其中 config 是 RunnableConfig
    async def finalize_wrapper(
        state: SalesEmailState,
        config: RunnableConfig | dict | None = None,
    ) -> SalesEmailState:
        """Wrapper for finalize node: run_id 优先从 state 取（调用方注入），否则从 config 回退."""
        run_id = state.run_id or ""
        if not run_id and config:
            configurable = (
                config.get("configurable", {})
                if isinstance(config, dict)
                else getattr(config, "configurable", None) or {}
            )
            if isinstance(configurable, dict):
                run_id = configurable.get("thread_id", "")
        return await finalize(state, db_repo, run_id)
    
    graph.add_node("check_idempotency", check_idempotency_wrapper)
    graph.add_node("load_masterdata", load_masterdata_wrapper)
    graph.add_node("match_contact", match_contact)
    graph.add_node("detect_contract_signal", detect_contract_signal)
    graph.add_node("match_customer", match_customer_wrapper)
    graph.add_node("upload_pdf", upload_pdf_wrapper)
    graph.add_node("call_dify_contract", call_dify_contract_wrapper)
    graph.add_node("call_dify_order_payload", call_dify_order_payload_wrapper)
    graph.add_node("call_gateway", call_gateway_wrapper)
    graph.add_node("notify_sales", notify_sales_wrapper)
    graph.add_node("finalize", finalize_wrapper)

    # Define edges（check_idempotency 仅用条件边分支，不重复加静态边，避免并行多路更新导致状态错乱）
    graph.set_entry_point("check_idempotency")

    graph.add_edge("load_masterdata", "match_contact")
    graph.add_edge("match_contact", "detect_contract_signal")
    graph.add_edge("detect_contract_signal", "match_customer")
    graph.add_edge("match_customer", "call_dify_contract")
    graph.add_edge("call_dify_contract", "call_dify_order_payload")
    graph.add_edge("call_dify_order_payload", "call_gateway")
    graph.add_edge("call_gateway", "upload_pdf")
    graph.add_edge("upload_pdf", "notify_sales")
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

    # Compile with checkpoint（checkpointer 由调用方传入：RedisCheckpointStore.get_checkpoint_saver_sync() 或 MemorySaver()）
    return graph.compile(checkpointer=checkpointer)

