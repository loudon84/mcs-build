"""Call Dify contract recognition node."""

from mcs_contracts import DifyContractResult
from errors import DIFY_CONTRACT_FAILED, OrchestratorError
from graphs.sales_email.state import SalesEmailState
from settings import Settings
from tools.dify_client import DifyClient


async def node_call_dify_contract(
    state: SalesEmailState,
    dify_client: DifyClient,
    settings: Settings | None = None,
) -> SalesEmailState:
    """Call Dify contract recognition chatflow.
    
    If settings is provided and DIFY_CONF contains 'sales_email-call_dify_contract',
    uses the configured url, path, and token. Otherwise, uses the provided dify_client.
    """
    if not state.matched_customer or not state.file_upload or not state.file_upload.ok:
        return state

    customer = state.masterdata.get_customer_by_id(state.matched_customer.customer_id) if state.masterdata else None
    if not customer:
        return state

    # 尝试从 DIFY_CONF 配置中读取节点专用配置
    client_to_use = dify_client
    if settings:
        node_config = settings.get_dify_node_config("sales_email-call_dify_contract")
        if node_config and node_config.get("url") and node_config.get("token"):
            # 使用配置中的 url、path、token 创建新的客户端
            client_to_use = DifyClient(
                base_url=node_config["url"],
                app_key=node_config["token"],
                api_path=node_config.get("path", "/v1/chat-messages"),
            )

    inputs = {
        "customer_id": customer.customer_id,
        "customer_num": customer.customer_num,
    }

    files = [
        {
            "type": "file",
            "transfer_method": "remote_url",
            "url": state.file_upload.file_url,
        }
    ]

    result = await client_to_use.chatflow_async(
        query="识别采购合同",
        user=state.email_event.from_email,
        inputs=inputs,
        files=files,
    )

    contract_result = DifyContractResult(**result)
    state.contract_result = contract_result

    if not contract_result.ok:
        state.add_error(
            DIFY_CONTRACT_FAILED,
            contract_result.errors[0].reason if contract_result.errors else "Dify contract recognition failed",
        )

    return state

