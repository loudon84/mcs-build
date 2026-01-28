"""Load masterdata node."""

from mcs_contracts import ErrorInfo
from mcs_orchestrator.errors import MASTERDATA_INVALID, OrchestratorError
from mcs_orchestrator.graphs.sales_email.state import SalesEmailState
from mcs_orchestrator.observability.retry import retry_with_backoff
from mcs_orchestrator.tools.masterdata_client import MasterDataClient


@retry_with_backoff(max_retries=3)
async def node_load_masterdata(
    state: SalesEmailState,
    masterdata_client: MasterDataClient,
) -> SalesEmailState:
    """Load master data from service (with caching)."""
    try:
        masterdata = masterdata_client.get_all()
        state.masterdata = masterdata
        return state
    except Exception as e:
        state.add_error(
            MASTERDATA_INVALID,
            f"Failed to load master data: {str(e)}",
        )
        raise OrchestratorError(MASTERDATA_INVALID, f"Failed to load master data: {str(e)}") from e

