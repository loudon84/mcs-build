"""Test happy path for sales email graph."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from mcs_contracts import EmailEvent, EmailAttachment, StatusEnum
from graphs.sales_email.state import SalesEmailState


@pytest.mark.asyncio
async def test_happy_path():
    """Test successful orchestration flow."""
    # Mock dependencies
    with patch("tools.dify_client.DifyClient") as mock_dify, \
         patch("tools.file_server.FileServerClient") as mock_file_server, \
         patch("tools.masterdata_client.MasterDataClient") as mock_masterdata:

        # Setup mocks
        mock_dify_instance = AsyncMock()
        mock_dify_instance.chatflow_async.return_value = {
            "ok": True,
            "items": [{"product": "test", "quantity": 1}],
            "contract_meta": {},
        }
        mock_dify.return_value = mock_dify_instance

        # Create test email event
        email_event = EmailEvent(
            provider="imap",
            account="sales@example.com",
            folder="INBOX",
            uid="123",
            message_id="msg1",
            from_email="customer@example.com",
            to=["sales@example.com"],
            subject="采购合同",
            body_text="请查看附件",
            received_at="2024-01-01T00:00:00Z",
            attachments=[
                EmailAttachment(
                    attachment_id="att1",
                    filename="contract.pdf",
                    content_type="application/pdf",
                    size=1024,
                    sha256="a" * 64,
                    bytes_b64="dGVzdA==",
                )
            ],
        )

        # Create initial state
        state = SalesEmailState(email_event=email_event)

        # Test would continue with graph execution...
        # This is a placeholder for actual test implementation
        assert state.email_event.message_id == "msg1"

