"""Common types and utilities for MCS contracts."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class StatusEnum(str, Enum):
    """Orchestration status enumeration."""

    IGNORED = "IGNORED"
    UNKNOWN_CONTACT = "UNKNOWN_CONTACT"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    CONTRACT_PARSE_FAILED = "CONTRACT_PARSE_FAILED"
    ORDER_PAYLOAD_BLOCKED = "ORDER_PAYLOAD_BLOCKED"
    ERP_ORDER_FAILED = "ERP_ORDER_FAILED"
    SUCCESS = "SUCCESS"
    PENDING = "PENDING"
    FAILED = "FAILED"
    RUNNING = "RUNNING"


class ErrorInfo(BaseModel):
    """Error information structure."""

    code: str = Field(..., description="Error code")
    reason: str = Field(..., description="Error reason")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


def now_iso() -> str:
    """Get current time in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


# Type aliases
DatetimeStr = str
EmailStrType = EmailStr

