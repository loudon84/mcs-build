"""Orchestration API routes."""

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import (
    get_db_session,
    get_dify_contract_client,
    get_dify_order_client,
    get_file_server,
    get_gateway_service,
    get_mailer,
    get_masterdata_service,
    get_orchestration_service,
    get_repo,
    get_settings,
)
from api.schemas import ManualReviewRequest, ManualReviewResponse, ReplayRequest, RunRequest, RunResponse
from mcs_contracts import OrchestratorRunResult, StatusEnum
from observability.logging import get_logger
from services.gateway_service import GatewayService
from services.masterdata_service import MasterDataService
from services.orchestration_service import OrchestrationService
from settings import Settings
from tools.dify_client import DifyClient
from tools.file_server import FileServerClient
from tools.mailer import Mailer

router = APIRouter(prefix="/v1/orchestrations", tags=["orchestrations"])
logger = get_logger()


@router.post("/sales-email/run", response_model=RunResponse)
async def run_sales_email(
    request: RunRequest,
    orchestration_service: Annotated[OrchestrationService, Depends(get_orchestration_service)],
):
    """Run sales email orchestration."""
    try:
        result = await orchestration_service.run_sales_email(request)
        return result
    except Exception as e:
        logger.error(
            "Sales email orchestration failed",
            extra={"message_id": request.message_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestration failed: {str(e)}",
        ) from e


@router.post("/sales-email/replay", response_model=RunResponse)
async def replay_sales_email(
    request: ReplayRequest,
    orchestration_service: Annotated[OrchestrationService, Depends(get_orchestration_service)],
):
    """Replay sales email orchestration by message_id or idempotency_key."""
    try:
        result = await orchestration_service.replay_sales_email(request)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Replay failed: {str(e)}",
        ) from e


@router.post("/sales-email/manual-review/submit", response_model=ManualReviewResponse)
async def submit_manual_review(
    request: ManualReviewRequest,
    orchestration_service: Annotated[OrchestrationService, Depends(get_orchestration_service)],
):
    """Submit manual review decision and resume execution."""
    try:
        result = await orchestration_service.submit_manual_review(request)
        return result
    except Exception as e:
        logger.error(
            "Manual review submission failed",
            extra={"run_id": request.run_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Manual review submission failed: {str(e)}",
        ) from e
