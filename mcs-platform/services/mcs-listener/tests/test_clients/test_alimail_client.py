"""Tests for Alimail client."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from mcs_listener.clients.alimail_client import AlimailClient, OAuthManager
from mcs_listener.clients.exceptions import AlimailAuthError, AlimailAPIError


@pytest.mark.asyncio
async def test_oauth_manager_get_token():
    """Test OAuth token retrieval."""
    manager = OAuthManager("test_client_id", "test_client_secret")
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance
        
        token = await manager.get_token()
        
        assert token == "test_token_123"
        assert manager.is_token_valid()


@pytest.mark.asyncio
async def test_oauth_manager_token_caching():
    """Test OAuth token caching."""
    manager = OAuthManager("test_client_id", "test_client_secret")
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance
        
        # First call
        token1 = await manager.get_token()
        # Second call should use cache
        token2 = await manager.get_token()
        
        assert token1 == token2 == "test_token_123"
        # Should only call API once
        assert mock_client_instance.__aenter__.return_value.post.call_count == 1


@pytest.mark.asyncio
async def test_oauth_manager_refresh_token():
    """Test OAuth token refresh."""
    manager = OAuthManager("test_client_id", "test_client_secret")
    
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "new_token_456",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance
        
        token = await manager.refresh_token()
        
        assert token == "new_token_456"


@pytest.mark.asyncio
async def test_alimail_client_list_mail_folders():
    """Test listing mail folders."""
    client = AlimailClient("test_client_id", "test_client_secret", "test@example.com")
    
    with patch.object(client.oauth_manager, "get_token", return_value="test_token"):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "value": [
                    {"id": "1", "displayName": "发件箱"},
                    {"id": "2", "displayName": "收件箱"},
                ]
            }
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.request = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance
            
            folders = await client.list_mail_folders()
            
            assert len(folders) == 2
            assert folders[0]["id"] == "1"
            assert folders[1]["id"] == "2"


@pytest.mark.asyncio
async def test_alimail_client_list_messages():
    """Test listing messages."""
    client = AlimailClient("test_client_id", "test_client_secret", "test@example.com")
    
    with patch.object(client.oauth_manager, "get_token", return_value="test_token"):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "messages": [
                    {"id": "msg1", "subject": "Test 1"},
                    {"id": "msg2", "subject": "Test 2"},
                ],
                "hasMore": False,
                "nextCursor": "",
            }
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.request = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance
            
            result = await client.list_messages("2")
            
            assert "messages" in result
            assert len(result["messages"]) == 2


@pytest.mark.asyncio
async def test_alimail_client_get_message():
    """Test getting message details."""
    client = AlimailClient("test_client_id", "test_client_secret", "test@example.com")
    
    with patch.object(client.oauth_manager, "get_token", return_value="test_token"):
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "msg1",
                "subject": "Test Subject",
                "from": {"email": "sender@example.com"},
                "body": {"bodyText": "Test body"},
            }
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.request = AsyncMock(return_value=mock_response)
            mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_client_instance
            
            message = await client.get_message("msg1")
            
            assert message["id"] == "msg1"
            assert message["subject"] == "Test Subject"


@pytest.mark.asyncio
async def test_alimail_client_auto_retry_on_401():
    """Test automatic token refresh on 401 error."""
    client = AlimailClient("test_client_id", "test_client_secret", "test@example.com")
    
    with patch.object(client.oauth_manager, "get_token", side_effect=["old_token", "new_token"]):
        with patch.object(client.oauth_manager, "refresh_token", return_value="new_token"):
            with patch("httpx.AsyncClient") as mock_client:
                # First response: 401
                mock_response_401 = MagicMock()
                mock_response_401.status_code = 401
                
                # Second response: 200
                mock_response_200 = MagicMock()
                mock_response_200.json.return_value = {"value": []}
                mock_response_200.status_code = 200
                mock_response_200.raise_for_status = MagicMock()
                
                mock_client_instance = AsyncMock()
                mock_client_instance.request = AsyncMock(
                    side_effect=[mock_response_401, mock_response_200]
                )
                mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
                mock_client_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_client_instance
                
                folders = await client.list_mail_folders()
                
                # Should have retried with new token
                assert mock_client_instance.request.call_count == 2
