"""Tests for Alimail listener."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from mcs_listener.listeners.alimail_listener import AlimailListener


@pytest.mark.asyncio
async def test_alimail_listener_connect():
    """Test Alimail listener connection."""
    listener = AlimailListener(
        client_id="test_id",
        client_secret="test_secret",
        email_account="test@example.com",
    )
    
    with patch.object(listener.client, "get_access_token", return_value="test_token"):
        await listener.connect()
        
        # Should not raise exception
        assert True


@pytest.mark.asyncio
async def test_alimail_listener_poll_new_messages():
    """Test polling new messages."""
    listener = AlimailListener(
        client_id="test_id",
        client_secret="test_secret",
        email_account="test@example.com",
        folder_id="2",
    )
    
    with patch.object(
        listener.client,
        "list_messages",
        return_value={
            "messages": [
                {"id": "msg1", "subject": "Test 1"},
                {"id": "msg2", "subject": "Test 2"},
            ],
            "hasMore": False,
            "nextCursor": "",
        },
    ):
        message_ids = await listener.poll_new_messages()
        
        assert len(message_ids) == 2
        assert "msg1" in message_ids
        assert "msg2" in message_ids


@pytest.mark.asyncio
async def test_alimail_listener_fetch_message():
    """Test fetching message content."""
    listener = AlimailListener(
        client_id="test_id",
        client_secret="test_secret",
        email_account="test@example.com",
    )
    
    mock_message = {
        "id": "msg1",
        "mailId": "mail-id-123",
        "subject": "Test Subject",
        "from": {"email": "sender@example.com", "name": "Sender"},
        "toRecipients": [{"email": "recipient@example.com", "name": "Recipient"}],
        "ccRecipients": [{"email": "cc@example.com", "name": "CC"}],
        "body": {"bodyText": "Test body", "bodyHtml": "<p>Test body</p>"},
        "receivedDateTime": "2024-01-01T10:00:00Z",
        "hasAttachments": False,
    }
    
    with patch.object(listener.client, "get_message", return_value=mock_message):
        with patch.object(listener.client, "list_attachments", return_value=[]):
            message_data = await listener.fetch_message("msg1")
            
            assert message_data["uid"] == "msg1"
            assert message_data["message_id"] == "mail-id-123"
            assert message_data["subject"] == "Test Subject"
            assert message_data["from"] == "sender@example.com"
            assert "recipient@example.com" in message_data["to"]
            assert "cc@example.com" in message_data["cc"]
            assert message_data["body"] == "Test body"
            assert message_data["body_html"] == "<p>Test body</p>"
            assert message_data["provider"] == "alimail"
            assert message_data["account"] == "test@example.com"


@pytest.mark.asyncio
async def test_alimail_listener_fetch_message_with_attachments():
    """Test fetching message with attachments."""
    listener = AlimailListener(
        client_id="test_id",
        client_secret="test_secret",
        email_account="test@example.com",
    )
    
    mock_message = {
        "id": "msg1",
        "mailId": "mail-id-123",
        "subject": "Test Subject",
        "from": {"email": "sender@example.com"},
        "toRecipients": [],
        "ccRecipients": [],
        "body": {"bodyText": "Test body"},
        "receivedDateTime": "2024-01-01T10:00:00Z",
        "hasAttachments": True,
    }
    
    mock_attachments = [
        {"id": "att1", "name": "file1.pdf", "contentType": "application/pdf"},
    ]
    
    with patch.object(listener.client, "get_message", return_value=mock_message):
        with patch.object(listener.client, "list_attachments", return_value=mock_attachments):
            with patch.object(
                listener.client, "download_attachment", return_value=b"file content"
            ):
                message_data = await listener.fetch_message("msg1")
                
                assert len(message_data["attachments"]) == 1
                assert message_data["attachments"][0]["filename"] == "file1.pdf"
                assert message_data["attachments"][0]["content_type"] == "application/pdf"
                assert message_data["attachments"][0]["payload"] == b"file content"


@pytest.mark.asyncio
async def test_alimail_listener_channel_type():
    """Test channel type property."""
    listener = AlimailListener(
        client_id="test_id",
        client_secret="test_secret",
        email_account="test@example.com",
    )
    
    assert listener.channel_type == "email"


@pytest.mark.asyncio
async def test_alimail_listener_disconnect():
    """Test disconnecting listener."""
    listener = AlimailListener(
        client_id="test_id",
        client_secret="test_secret",
        email_account="test@example.com",
    )
    
    with patch.object(listener.client, "close", return_value=None):
        await listener.disconnect()
        
        # Should not raise exception
        assert True
