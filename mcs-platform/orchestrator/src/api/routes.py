"""API routes for mcs-orchestrator."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from mcs_contracts import EmailEvent, ManualReviewSubmitResponse, OrchestratorRunResult, StatusEnum, now_iso
from api.deps import (
    get_db_session,
    get_dify_contract_client,
    get_dify_order_client,
    get_file_server,
    get_gateway_service,
    get_mailer,
    get_masterdata_service,
    get_repo,
    get_settings,
)
from api.schemas import (
    ManualReviewRequest,
    ManualReviewResponse,
    ReplayRequest,
    RunRequest,
    RunResponse,
)
from db.checkpoint.redis_checkpoint import RedisCheckpointStore
from db.repo import OrchestratorRepo
from errors import (
    INVALID_DECISION,
    PERMISSION_DENIED,
    RUN_NOT_IN_MANUAL_REVIEW,
    OrchestratorError,
)
from graphs.registry import GraphRegistry
from graphs.sales_email.graph import build_sales_email_graph
from graphs.sales_email.resume import determine_resume_node, resume_from_node
from graphs.sales_email.state import SalesEmailState
from observability.logging import get_logger
from observability.redaction import redact_dict
from services.gateway_service import GatewayService
from services.masterdata_service import MasterDataService
from settings import Settings
from tools.dify_client import DifyClient
from tools.file_server import FileServerClient
from tools.mailer import Mailer

router = APIRouter(prefix="/v1/orchestrations", tags=["orchestrations"])
logger = get_logger()


@router.post("/sales-email/run", response_model=RunResponse)
async def run_sales_email(
    request: RunRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_db_session)],
    repo: Annotated[OrchestratorRepo, Depends(get_repo)],
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
    file_server: Annotated[FileServerClient, Depends(get_file_server)],
    dify_contract_client: Annotated[DifyClient, Depends(get_dify_contract_client)],
    dify_order_client: Annotated[DifyClient, Depends(get_dify_order_client)],
    mailer: Annotated[Mailer, Depends(get_mailer)],
    gateway_service: Annotated[GatewayService, Depends(get_gateway_service)],
):
    """Run sales email orchestration."""
    run_id = str(uuid4())
    started_at = now_iso()

    logger.info(
        "Starting sales email orchestration",
        extra={
            "run_id": run_id,
            "message_id": request.message_id,
            "from_email": request.from_email,
        },
    )

    try:
        # Create run record
        repo.create_run(
            run_id=run_id,
            message_id=request.message_id,
            status=StatusEnum.PENDING.value,
            started_at=started_at,
        )

        # Build graph（checkpoint_backend=memory 时用 MemorySaver，无需 Redis JSON）
        if settings.checkpoint_backend == "memory":
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()
        else:
            checkpoint_store = RedisCheckpointStore(settings)
            await checkpoint_store.initialize()
            checkpointer = checkpoint_store.get_checkpoint_saver_sync()

        graph = build_sales_email_graph(
            settings=settings,
            db_repo=repo,
            checkpointer=checkpointer,
            masterdata_service=masterdata_service,
            file_server=file_server,
            dify_contract_client=dify_contract_client,
            dify_order_client=dify_order_client,
            mailer=mailer,
            gateway_service=gateway_service,
        )

        # Initialize state（run_id 写入 state，finalize 用其更新 DB）
        initial_state = SalesEmailState(
            email_event=request,
            run_id=run_id,
            started_at=started_at,
        )

        # Run graph
        result = await graph.ainvoke(initial_state.model_dump(), {"configurable": {"thread_id": run_id}})
        final_state = SalesEmailState(**result)

        # Create result
        result = OrchestratorRunResult(
            run_id=run_id,
            message_id=request.message_id,
            status=final_state.final_status or StatusEnum.FAILED,
            started_at=started_at,
            finished_at=final_state.finished_at,
            idempotency_key=final_state.idempotency_key,
            customer_id=final_state.matched_customer.customer_id if final_state.matched_customer else None,
            contact_id=final_state.matched_contact.contact_id if final_state.matched_contact else None,
            file_url=final_state.file_upload.file_url if final_state.file_upload else None,
            sales_order_no=final_state.erp_result.sales_order_no if final_state.erp_result else None,
            order_url=final_state.erp_result.order_url if final_state.erp_result else None,
            warnings=final_state.warnings,
            errors=final_state.errors,
        )

        logger.info(
            "Sales email orchestration completed",
            extra={
                "run_id": run_id,
                "status": result.status.value if result.status else None,
            },
        )

        return result
    except Exception as e:
        # Update run status to failed
        logger.error(
            "Sales email orchestration failed",
            extra={
                "run_id": run_id,
                "message_id": request.message_id,
                "error": str(e),
            },
            exc_info=True,
        )
        try:
            repo.update_run_status(run_id=run_id, status=StatusEnum.FAILED.value)
        except Exception as update_error:
            logger.error(
                "Failed to update run status",
                extra={
                    "run_id": run_id,
                    "error": str(update_error),
                },
                exc_info=True,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration failed: {str(e)}",
        ) from e


@router.post("/sales-email/replay", response_model=RunResponse)
async def replay_sales_email(
    request: ReplayRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_db_session)],
    repo: Annotated[OrchestratorRepo, Depends(get_repo)],
):
    """Replay sales email orchestration by message_id or idempotency_key."""
    # Find previous run
    if request.message_id:
        previous_run = repo.find_run_by_message_id(request.message_id)
        if not previous_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run not found for message_id: {request.message_id}",
            )
        # Return previous result
        return OrchestratorRunResult(
            run_id=previous_run.run_id,
            message_id=previous_run.message_id,
            status=StatusEnum(previous_run.status),
            started_at=previous_run.started_at.isoformat(),
            finished_at=previous_run.finished_at.isoformat() if previous_run.finished_at else None,
            errors=previous_run.errors_json or [],
            warnings=previous_run.warnings_json or [],
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either message_id or idempotency_key must be provided",
        )


@router.post("/sales-email/manual-review/submit", response_model=ManualReviewResponse)
async def submit_manual_review(
    request: ManualReviewRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_db_session)],
    repo: Annotated[OrchestratorRepo, Depends(get_repo)],
    masterdata_service: Annotated[MasterDataService, Depends(get_masterdata_service)],
    file_server: Annotated[FileServerClient, Depends(get_file_server)],
    dify_contract_client: Annotated[DifyClient, Depends(get_dify_contract_client)],
    dify_order_client: Annotated[DifyClient, Depends(get_dify_order_client)],
    mailer: Annotated[Mailer, Depends(get_mailer)],
    gateway_service: Annotated[GatewayService, Depends(get_gateway_service)],
):
    """Submit manual review decision and resume execution."""
    # Validate run exists and is in MANUAL_REVIEW status
    try:
        run = repo.assert_run_in_status(request.run_id, StatusEnum.MANUAL_REVIEW.value)
    except OrchestratorError as e:
        if e.code == "RUN_NOT_FOUND":
            return ManualReviewSubmitResponse(
                ok=False,
                run_id=request.run_id,
                error_code="RUN_NOT_FOUND",
                reason=str(e),
            )
        elif e.code == RUN_NOT_IN_MANUAL_REVIEW:
            return ManualReviewSubmitResponse(
                ok=False,
                run_id=request.run_id,
                error_code=RUN_NOT_IN_MANUAL_REVIEW,
                reason=str(e),
            )
        raise

    # Validate message_id consistency
    if request.message_id and request.message_id != run.message_id:
        return ManualReviewSubmitResponse(
            ok=False,
            run_id=request.run_id,
            error_code=INVALID_DECISION,
            reason=f"Message ID mismatch: expected {run.message_id}, got {request.message_id}",
        )

    # Validate tenant_id (if present in run state)
    if run.state_json and "tenant_id" in run.state_json:
        auth_tenant_id = request.auth.get("tenant_id")
        if not auth_tenant_id or auth_tenant_id != run.state_json.get("tenant_id"):
            return ManualReviewSubmitResponse(
                ok=False,
                run_id=request.run_id,
                error_code=PERMISSION_DENIED,
                reason="Tenant ID mismatch",
            )

    # Validate scopes
    scopes = request.auth.get("scopes", [])
    required_scope = "mcs:sales_email:manual_review"
    if required_scope not in scopes:
        return ManualReviewSubmitResponse(
            ok=False,
            run_id=request.run_id,
            error_code=PERMISSION_DENIED,
            reason=f"Missing required scope: {required_scope}",
        )

    # Validate decision fields
    decision = request.decision
    if decision.action == "RESUME":
        if not decision.selected_customer_id:
            return ManualReviewSubmitResponse(
                ok=False,
                run_id=request.run_id,
                error_code=INVALID_DECISION,
                reason="selected_customer_id is required for RESUME action",
            )
        # selected_attachment_id required if multiple PDFs or not already selected
        if not decision.selected_attachment_id and run.state_json:
            manual_review = run.state_json.get("manual_review", {})
            candidates = manual_review.get("candidates", {})
            if len(candidates.get("pdfs", [])) > 1:
                return ManualReviewSubmitResponse(
                    ok=False,
                    run_id=request.run_id,
                    error_code=INVALID_DECISION,
                    reason="selected_attachment_id is required when multiple PDFs exist",
                )
    elif decision.action == "BLOCK":
        if not decision.comment:
            return ManualReviewSubmitResponse(
                ok=False,
                run_id=request.run_id,
                error_code=INVALID_DECISION,
                reason="comment is required for BLOCK action",
            )
    else:
        return ManualReviewSubmitResponse(
            ok=False,
            run_id=request.run_id,
            error_code=INVALID_DECISION,
            reason=f"Invalid action: {decision.action}",
        )

    # Prepare audit payload (redacted)
    audit_payload = {
        "run_id": request.run_id,
        "message_id": run.message_id,
        "reason_code": run.state_json.get("manual_review", {}).get("reason_code") if run.state_json else None,
        "decision": {
            "action": decision.action,
            "selected_customer_id": decision.selected_customer_id,
            "selected_contact_id": decision.selected_contact_id,
            "selected_attachment_id": decision.selected_attachment_id,
            "comment": decision.comment,
        },
        "operator": {
            "user_id": request.operator.get("user_id"),
            "user_name": request.operator.get("user_name"),
        },
        "auth": {
            "tenant_id": request.auth.get("tenant_id"),
            "request_id": request.auth.get("request_id"),
        },
    }
    redacted_payload = redact_dict(audit_payload)

    # Write audit event
    audit_event = repo.write_manual_review_decision(request.run_id, redacted_payload)

    if decision.action == "BLOCK":
        # Update run status to keep MANUAL_REVIEW
        repo.update_run_status(
            run_id=request.run_id,
            status=StatusEnum.MANUAL_REVIEW.value,
            state_json={
                **(run.state_json or {}),
                "manual_review": {
                    **(run.state_json.get("manual_review", {}) if run.state_json else {}),
                    "decision": {
                        "action": decision.action,
                        "comment": decision.comment,
                        "decided_at": now_iso(),
                        "operator_user_id": request.operator.get("user_id"),
                        "request_id": request.auth.get("request_id"),
                    },
                },
            },
        )

        return ManualReviewSubmitResponse(
            ok=True,
            status="BLOCKED",
            final_status=StatusEnum.MANUAL_REVIEW,
            audit_id=str(audit_event.id),
            run_id=request.run_id,
        )

    # RESUME action - resume from appropriate node
    try:
        # Load state from checkpoint（须与 run 时使用相同 backend，memory 时仅同进程内可 resume）
        if settings.checkpoint_backend == "memory":
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()
        else:
            checkpoint_store = RedisCheckpointStore(settings)
            await checkpoint_store.initialize()
            checkpointer = checkpoint_store.get_checkpoint_saver_sync()

        graph = build_sales_email_graph(
            settings=settings,
            db_repo=repo,
            checkpointer=checkpointer,
            masterdata_service=masterdata_service,
            file_server=file_server,
            dify_contract_client=dify_contract_client,
            dify_order_client=dify_order_client,
            mailer=mailer,
            gateway_service=gateway_service,
        )

        # Get current state from checkpoint
        config = {"configurable": {"thread_id": request.run_id}}
        current_state_dict = await graph.aget_state(config)
        if not current_state_dict or not current_state_dict.values:
            return ManualReviewSubmitResponse(
                ok=False,
                run_id=request.run_id,
                error_code="STATE_NOT_FOUND",
                reason="Could not retrieve state from checkpoint",
            )

        state = SalesEmailState(**current_state_dict.values)

        # Prepare patch
        patch = {
            "selected_customer_id": decision.selected_customer_id,
            "selected_contact_id": decision.selected_contact_id,
            "selected_attachment_id": decision.selected_attachment_id,
        }

        # Determine resume node
        resume_node = determine_resume_node(state, patch)

        # Apply patch and resume
        masterdata = masterdata_service.get_all()
        patched_state = await resume_from_node(state, resume_node, patch, repo, masterdata)

        # Update run status to RUNNING
        repo.update_run_status(
            run_id=request.run_id,
            status=StatusEnum.RUNNING.value,
        )

        # Continue execution from resume node
        # Update state in checkpoint first
        await graph.aupdate_state(config, patched_state.model_dump())

        # Resume from the specified node using astream
        # LangGraph will continue from the checkpoint state
        final_state_dict = None
        async for chunk in graph.astream(None, config):
            # Get the last chunk which contains the final state
            if isinstance(chunk, dict):
                for node_name, node_state in chunk.items():
                    if node_state and isinstance(node_state, dict):
                        final_state_dict = node_state
                    elif hasattr(node_state, "values"):
                        final_state_dict = node_state.values

        # If we got a final state, use it; otherwise get from checkpoint
        if final_state_dict:
            final_state = SalesEmailState(**final_state_dict)
        else:
            # Fallback: get final state from checkpoint
            checkpoint_state = await graph.aget_state(config)
            if checkpoint_state and checkpoint_state.values:
                final_state = SalesEmailState(**checkpoint_state.values)
            else:
                final_state = patched_state

        # Update final status
        repo.update_run_status(
            run_id=request.run_id,
            status=final_state.final_status.value if final_state.final_status else StatusEnum.FAILED.value,
            finished_at=final_state.finished_at,
        )

        return ManualReviewSubmitResponse(
            ok=True,
            status="RESUMING",
            resume={
                "from_node": resume_node,
                "planned_path": [resume_node, "upload_pdf", "call_dify_contract", "call_dify_order_payload", "call_gateway", "notify_sales", "finalize"],
            },
            audit_id=str(audit_event.id),
            run_id=request.run_id,
        )

    except Exception as e:
        return ManualReviewSubmitResponse(
            ok=False,
            run_id=request.run_id,
            error_code="RESUME_FAILED",
            reason=f"Failed to resume execution: {str(e)}",
        )


@router.get("/healthz")
async def healthz(
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_db_session)],
):
    """Health check endpoint."""
    from observability.monitoring import check_health

    health_status = await check_health(settings, session)
    return health_status

