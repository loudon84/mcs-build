"""Orchestration service for sales email workflows."""

from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.schemas import ManualReviewRequest, ManualReviewResponse, ReplayRequest, RunRequest, RunResponse
from db.checkpoint.redis_checkpoint import RedisCheckpointStore
from db.repo import OrchestratorRepo
from errors import (
    INVALID_DECISION,
    PERMISSION_DENIED,
    RUN_NOT_IN_MANUAL_REVIEW,
    OrchestratorError,
)
from graphs.sales_email.graph import build_sales_email_graph
from graphs.sales_email.resume import determine_resume_node, resume_from_node
from graphs.sales_email.state import SalesEmailState
from mcs_contracts import EmailEvent, ManualReviewSubmitResponse, OrchestratorRunResult, StatusEnum, now_iso
from observability.logging import get_logger
from observability.redaction import redact_dict
from services.gateway_service import GatewayService
from services.masterdata_service import MasterDataService
from settings import Settings
from tools.dify_client import DifyClient
from tools.file_server import FileServerClient
from tools.mailer import Mailer

logger = get_logger()


class OrchestrationService:
    """Service for orchestration operations."""

    def __init__(
        self,
        settings: Settings,
        repo: OrchestratorRepo,
        masterdata_service: MasterDataService,
        file_server: FileServerClient,
        dify_contract_client: DifyClient,
        dify_order_client: DifyClient,
        mailer: Mailer,
        gateway_service: GatewayService,
    ):
        """Initialize orchestration service."""
        self.settings = settings
        self.repo = repo
        self.masterdata_service = masterdata_service
        self.file_server = file_server
        self.dify_contract_client = dify_contract_client
        self.dify_order_client = dify_order_client
        self.mailer = mailer
        self.gateway_service = gateway_service

    async def run_sales_email(self, email_event: EmailEvent | RunRequest) -> OrchestratorRunResult:
        """Run sales email orchestration."""
        # RunRequest is an alias for EmailEvent, so use directly
        request = email_event

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
            self.repo.create_run(
                run_id=run_id,
                message_id=request.message_id,
                status=StatusEnum.PENDING.value,
                started_at=started_at,
            )

            # Build graph（checkpoint_backend=memory 时用 MemorySaver，无需 Redis JSON；redis 时需 Redis Stack/RedisJSON）
            if self.settings.checkpoint_backend == "memory":
                from langgraph.checkpoint.memory import MemorySaver
                checkpointer = MemorySaver()
            else:
                checkpoint_store = RedisCheckpointStore(self.settings)
                await checkpoint_store.initialize()
                checkpointer = checkpoint_store.get_checkpoint_saver_sync()

            graph = build_sales_email_graph(
                settings=self.settings,
                db_repo=self.repo,
                checkpointer=checkpointer,
                masterdata_service=self.masterdata_service,
                file_server=self.file_server,
                dify_contract_client=self.dify_contract_client,
                dify_order_client=self.dify_order_client,
                mailer=self.mailer,
                gateway_service=self.gateway_service,
            )

            # Initialize state（run_id 写入 state，finalize 用其更新 DB，不依赖 config 传递）
            initial_state = SalesEmailState(
                email_event=request,
                run_id=run_id,
                started_at=started_at,
            )

            # Run graph
            result = await graph.ainvoke(
                initial_state.model_dump(),
                {"configurable": {"thread_id": run_id}},
            )
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
                self.repo.update_run_status(run_id=run_id, status=StatusEnum.FAILED.value)
            except Exception as update_error:
                logger.error(
                    "Failed to update run status",
                    extra={
                        "run_id": run_id,
                        "error": str(update_error),
                    },
                    exc_info=True,
                )
            raise

    async def replay_sales_email(self, request: ReplayRequest) -> OrchestratorRunResult:
        """Replay sales email orchestration by message_id or idempotency_key."""
        # Find previous run
        if request.message_id:
            previous_run = self.repo.find_run_by_message_id(request.message_id)
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

    async def submit_manual_review(self, request: ManualReviewRequest) -> ManualReviewResponse:
        """Submit manual review decision and resume execution."""
        # Validate run exists and is in MANUAL_REVIEW status
        try:
            run = self.repo.assert_run_in_status(request.run_id, StatusEnum.MANUAL_REVIEW.value)
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
        audit_event = self.repo.write_manual_review_decision(request.run_id, redacted_payload)

        if decision.action == "BLOCK":
            # Update run status to keep MANUAL_REVIEW
            self.repo.update_run_status(
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

        # RESUME action - resume from appropriate node（须与 run 时相同 checkpoint_backend）
        try:
            if self.settings.checkpoint_backend == "memory":
                from langgraph.checkpoint.memory import MemorySaver
                checkpointer = MemorySaver()
            else:
                checkpoint_store = RedisCheckpointStore(self.settings)
                await checkpoint_store.initialize()
                checkpointer = checkpoint_store.get_checkpoint_saver_sync()

            graph = build_sales_email_graph(
                settings=self.settings,
                db_repo=self.repo,
                checkpointer=checkpointer,
                masterdata_service=self.masterdata_service,
                file_server=self.file_server,
                dify_contract_client=self.dify_contract_client,
                dify_order_client=self.dify_order_client,
                mailer=self.mailer,
                gateway_service=self.gateway_service,
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
            masterdata = self.masterdata_service.get_all()
            patched_state = await resume_from_node(state, resume_node, patch, self.repo, masterdata)

            # Update run status to RUNNING
            self.repo.update_run_status(
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
                        final_state_dict = node_state

            if not final_state_dict:
                return ManualReviewSubmitResponse(
                    ok=False,
                    run_id=request.run_id,
                    error_code="EXECUTION_FAILED",
                    reason="Failed to resume execution",
                )

            final_state = SalesEmailState(**final_state_dict)

            # Update run status
            self.repo.update_run_status(
                run_id=request.run_id,
                status=final_state.final_status.value if final_state.final_status else StatusEnum.FAILED.value,
                finished_at=final_state.finished_at,
            )

            return ManualReviewSubmitResponse(
                ok=True,
                status="RESUMED",
                final_status=final_state.final_status or StatusEnum.FAILED,
                audit_id=str(audit_event.id),
                run_id=request.run_id,
            )

        except Exception as e:
            logger.error(
                "Failed to resume orchestration",
                extra={"run_id": request.run_id, "error": str(e)},
                exc_info=True,
            )
            return ManualReviewSubmitResponse(
                ok=False,
                run_id=request.run_id,
                error_code="RESUME_FAILED",
                reason=f"Failed to resume execution: {str(e)}",
            )