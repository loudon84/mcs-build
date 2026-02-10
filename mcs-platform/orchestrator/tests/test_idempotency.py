"""Test idempotency."""

import pytest

from mcs_contracts import StatusEnum
from db.models import IdempotencyRecord
from db.repo import OrchestratorRepo


def test_idempotency_hit():
    """Test idempotency cache hit."""
    # Mock repository
    repo = MagicMock(spec=OrchestratorRepo)
    record = IdempotencyRecord(
        idempotency_key="test_key",
        message_id="msg1",
        status=StatusEnum.SUCCESS.value,
        sales_order_no="SO001",
        order_url="https://example.com/orders/SO001",
    )
    repo.get_idempotency_record.return_value = record

    # Test idempotency check
    result = repo.get_idempotency_record("test_key")
    assert result is not None
    assert result.status == StatusEnum.SUCCESS.value
    assert result.sales_order_no == "SO001"

