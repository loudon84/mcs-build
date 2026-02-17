"""Middleware for FastAPI."""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from observability.logging import get_logger, setup_logging
from observability.redaction import redact_dict

logger = get_logger()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and propagate X-Request-ID."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with request ID."""
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        setup_logging(request_id=request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response."""
        request_id = getattr(request.state, "request_id", "unknown")

        # Log request (request_id 已由 RequestIdMiddleware 通过 setup_logging 注入到 LogRecord，勿在 extra 中重复传递)
        logger.info(
            "Request received",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
            },
        )

        try:
            response = await call_next(request)
            # Log response
            logger.info(
                "Request completed",
                extra={
                    "status_code": response.status_code,
                },
            )
            return response
        except Exception as e:
            logger.error(
                "Request failed",
                extra={
                    "error": str(e),
                },
                exc_info=True,
            )
            raise


class ExceptionMiddleware(BaseHTTPMiddleware):
    """Middleware for exception handling."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle exceptions."""
        try:
            return await call_next(request)
        except Exception as e:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                "Unhandled exception",
                extra={
                    "error": str(e),
                },
                exc_info=True,
            )
            from fastapi import HTTPException, status
            from fastapi.responses import JSONResponse

            if isinstance(e, HTTPException):
                raise

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                },
            )

