"""Test checkpoint store."""

import pytest

from db.checkpoint.postgres_checkpoint import PostgresCheckpointStore
from settings import Settings


@pytest.mark.asyncio
async def test_checkpoint_store():
    """Test checkpoint store initialization."""
    settings = Settings.from_env()
    checkpoint_store = PostgresCheckpointStore(settings)

    # Test initialization
    await checkpoint_store.initialize()
    saver = await checkpoint_store.get_checkpoint_saver()
    assert saver is not None

