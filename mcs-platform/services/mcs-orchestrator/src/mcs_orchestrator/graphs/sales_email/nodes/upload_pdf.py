"""Upload PDF node."""

import base64
import hashlib

from mcs_contracts import FileUploadResult, StatusEnum
from mcs_contracts.common import now_iso
from mcs_orchestrator.db.repo import OrchestratorRepo
from mcs_orchestrator.graphs.sales_email.state import SalesEmailState
from mcs_orchestrator.tools.file_server import FileServerClient


async def node_upload_pdf(
    state: SalesEmailState,
    file_server: FileServerClient,
    repo: OrchestratorRepo,
) -> SalesEmailState:
    """Upload PDF to file server."""
    if not state.pdf_attachment:
        return state

    # Decode base64 if available
    if state.pdf_attachment.bytes_b64:
        file_bytes = base64.b64decode(state.pdf_attachment.bytes_b64)
    else:
        # TODO: Fetch from email_listener API if bytes not available
        state.add_warning("PDF bytes not available, cannot upload")
        return state

    # Upload to file server
    upload_result = file_server.upload_file(
        file_bytes=file_bytes,
        filename=state.pdf_attachment.filename,
        content_type=state.pdf_attachment.content_type,
        sha256=state.pdf_attachment.sha256,
    )

    state.file_upload = upload_result

    # Update idempotency key now that we have file_sha256 and potentially customer_id
    if upload_result.ok and state.pdf_attachment.sha256:
        message_id = state.email_event.message_id
        file_sha256 = state.pdf_attachment.sha256
        customer_id = state.matched_customer.customer_id if state.matched_customer and state.matched_customer.ok else ""

        idempotency_key = hashlib.sha256(
            f"{message_id}:{file_sha256}:{customer_id}".encode()
        ).hexdigest()

        # Check if this idempotency key hits SUCCESS
        record = repo.get_idempotency_record(idempotency_key)
        if record and record.status == StatusEnum.SUCCESS.value:
            from mcs_contracts.results import ERPCreateOrderResult

            state.erp_result = ERPCreateOrderResult(
                ok=True,
                sales_order_no=record.sales_order_no,
                order_url=record.order_url,
            )
            state.final_status = StatusEnum.SUCCESS
            state.finished_at = now_iso()
            return state

        # Update idempotency record
        state.idempotency_key = idempotency_key
        repo.upsert_idempotency_record(
            idempotency_key=idempotency_key,
            message_id=message_id,
            status=StatusEnum.PENDING.value,
            file_sha256=file_sha256,
            customer_id=customer_id,
        )

    return state

