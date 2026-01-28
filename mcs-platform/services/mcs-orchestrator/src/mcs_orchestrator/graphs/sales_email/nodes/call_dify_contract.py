"""Call Dify contract recognition node."""

from mcs_contracts import DifyContractResult
from mcs_orchestrator.errors import DIFY_CONTRACT_FAILED, OrchestratorError
from mcs_orchestrator.graphs.sales_email.state import SalesEmailState
from mcs_orchestrator.tools.dify_client import DifyClient


async def node_call_dify_contract(
    state: SalesEmailState,
    dify_client: DifyClient,
) -> SalesEmailState:
    """Call Dify contract recognition chatflow."""
    if not state.matched_customer or not state.file_upload or not state.file_upload.ok:
        return state

    customer = state.masterdata.get_customer_by_id(state.matched_customer.customer_id) if state.masterdata else None
    if not customer:
        return state

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

    result = await dify_client.chatflow_async(
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

