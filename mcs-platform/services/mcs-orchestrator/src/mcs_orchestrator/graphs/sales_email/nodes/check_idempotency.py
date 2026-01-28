"""Check idempotency node."""

import hashlib
from datetime import datetime

from mcs_contracts import StatusEnum
from mcs_contracts.common import now_iso
from mcs_contracts.orchestrator import OrchestratorRunResult
from mcs_contracts.results import ERPCreateOrderResult
from mcs_orchestrator.db.repo import OrchestratorRepo
from mcs_orchestrator.graphs.sales_email.state import SalesEmailState


async def node_check_idempotency(
    state: SalesEmailState,
    repo: OrchestratorRepo,
) -> SalesEmailState:
    """Check idempotency - first step to avoid duplicate processing."""
    # At this point, we only have message_id, so we check by message_id first
    # Full idempotency key will be generated later when we have customer_id and file_sha256
    message_id = state.email_event.message_id

    # Try to find existing run by message_id
    existing_run = repo.find_run_by_message_id(message_id)
    if existing_run and existing_run.status == StatusEnum.SUCCESS.value:
        # Check if there's an idempotency record
        # For now, just proceed - full idempotency check happens after customer/file matching
        pass

    # Initial idempotency key (will be updated later when we have more info)
    # Use message_id only for initial check
    initial_key = hashlib.sha256(f"{message_id}:".encode()).hexdigest()
    state.idempotency_key = initial_key

    return state

