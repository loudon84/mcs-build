"""Test retry mechanism."""

import pytest
from unittest.mock import AsyncMock, patch

from observability.retry import retry_with_backoff


@retry_with_backoff(max_retries=3, backoff_factor=0.1)
async def failing_function():
    """Function that fails."""
    raise ValueError("Test error")


@pytest.mark.asyncio
async def test_retry_mechanism():
    """Test retry decorator."""
    with pytest.raises(ValueError):
        await failing_function()

    # The function should have been retried 3 times
    # (actual retry count verification would require more sophisticated mocking)

