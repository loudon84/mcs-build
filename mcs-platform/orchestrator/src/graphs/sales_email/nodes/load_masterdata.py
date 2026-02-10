"""Load masterdata node."""

from mcs_contracts import ErrorInfo
from errors import MASTERDATA_INVALID, OrchestratorError
from graphs.sales_email.state import SalesEmailState
from observability.retry import retry_with_backoff
from services.masterdata_service import MasterDataService


@retry_with_backoff(max_retries=3)
async def node_load_masterdata(
    state: SalesEmailState,
    masterdata_service: MasterDataService,
) -> SalesEmailState:
    """Load master data from service (with caching)."""
    try:
        masterdata = masterdata_service.get_all()
        state.masterdata = masterdata
        return state
    except Exception as e:
        state.add_error(
            MASTERDATA_INVALID,
            f"Failed to load master data: {str(e)}",
        )
        raise OrchestratorError(MASTERDATA_INVALID, f"Failed to load master data: {str(e)}") from e

