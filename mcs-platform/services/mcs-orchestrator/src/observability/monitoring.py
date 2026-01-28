"""Health check and monitoring."""

from typing import Any

import httpx
from prometheus_client import generate_latest
from sqlalchemy import text
from sqlalchemy.orm import Session

from settings import Settings


async def check_health(settings: Settings, db_session: Session) -> dict[str, Any]:
    """Perform health checks."""
    health_status = {
        "status": "healthy",
        "checks": {},
    }

    # Check database
    try:
        db_session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Dify (optional)
    if settings.dify_base_url:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.dify_base_url}/health",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    health_status["checks"]["dify"] = "ok"
                else:
                    health_status["checks"]["dify"] = f"error: status {response.status_code}"
        except Exception as e:
            health_status["checks"]["dify"] = f"error: {str(e)}"

    return health_status


def get_metrics() -> str:
    """Get Prometheus metrics."""
    return generate_latest().decode("utf-8")

