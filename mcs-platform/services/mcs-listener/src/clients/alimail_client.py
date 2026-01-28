"""Alimail REST API client."""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import httpx

from clients.exceptions import AlimailAuthError, AlimailAPIError, AlimailClientError


class OAuthManager:
    """OAuth 2.0 token manager with caching and auto-refresh."""

    def __init__(self, client_id: str, client_secret: str, base_url: str = "https://alimail-cn.aliyuncs.com"):
        """Initialize OAuth manager."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.token_url = f"{base_url}/oauth2/v2.0/token"
        
        # Token cache
        self._token: str | None = None
        self._expires_at: datetime | None = None
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        """Get valid access token (with caching and auto-refresh)."""
        async with self._lock:
            # Check if token is still valid (refresh 5 minutes before expiry)
            if self._token and self._expires_at:
                refresh_time = self._expires_at - timedelta(minutes=5)
                if datetime.now() < refresh_time:
                    return self._token
            
            # Token expired or not exists, refresh it
            return await self.refresh_token()

    async def refresh_token(self) -> str:
        """Refresh access token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                
                if "access_token" not in data:
                    raise AlimailAuthError("Missing access_token in response")
                
                self._token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self._expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                return self._token
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.text[:500] if e.response.text else ""
                error_detail = f" - {error_body}"
            except Exception:
                pass
            raise AlimailAuthError(f"Failed to get access token: {e.response.status_code}{error_detail}") from e
        except httpx.RequestError as e:
            raise AlimailClientError(f"Network error while getting token: {e}") from e
        except Exception as e:
            raise AlimailAuthError(f"Unexpected error while getting token: {e}") from e

    def is_token_valid(self) -> bool:
        """Check if current token is valid."""
        if not self._token or not self._expires_at:
            return False
        return datetime.now() < (self._expires_at - timedelta(minutes=5))


class AlimailClient:
    """Alimail REST API client."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        email_account: str,
        base_url: str = "https://alimail-cn.aliyuncs.com",
    ):
        """Initialize Alimail client."""
        self.email_account = email_account
        self.base_url = base_url
        self.oauth_manager = OAuthManager(client_id, client_secret, base_url)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _request(
        self,
        method: str,
        url: str,
        retry_on_auth_error: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with automatic token handling and retry."""
        client = await self._get_client()
        token = await self.oauth_manager.get_token()
        
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"bearer {token}"
        headers.setdefault("Content-Type", "application/json")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                
                # Handle 401 Unauthorized (token expired)
                if response.status_code == 401 and retry_on_auth_error and attempt < max_retries - 1:
                    # Refresh token and retry
                    await self.oauth_manager.refresh_token()
                    token = await self.oauth_manager.get_token()
                    headers["Authorization"] = f"bearer {token}"
                    continue
                
                # Raise exception for error status codes
                if response.status_code >= 400:
                    error_body = response.text[:500] if response.text else ""
                    raise AlimailAPIError(
                        f"API error: {response.status_code}",
                        status_code=response.status_code,
                        response_body=error_body,
                    )
                
                return response
                
            except httpx.RequestError as e:
                if attempt == max_retries - 1:
                    raise AlimailClientError(f"Network error after {max_retries} attempts: {e}") from e
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        raise AlimailClientError("Unexpected error in request")

    async def get_access_token(self) -> str:
        """Get access token."""
        return await self.oauth_manager.get_token()

    async def list_mail_folders(self) -> list[dict[str, Any]]:
        """List mail folders."""
        url = f"{self.base_url}/v2/users/{self.email_account}/mailFolders"
        response = await self._request("GET", url)
        data = response.json()
        return data.get("value", [])

    async def list_messages(
        self,
        folder_id: str,
        cursor: str = "",
        size: int = 100,
        orderby: str = "DES",
    ) -> dict[str, Any]:
        """List messages in folder (with pagination)."""
        url = f"{self.base_url}/v2/users/{self.email_account}/mailFolders/{folder_id}/messages"
        params = {
            "cursor": cursor,
            "size": str(size),
            "orderby": orderby,
        }
        response = await self._request("GET", url, params=params)
        return response.json()

    async def get_message(self, message_id: str) -> dict[str, Any]:
        """Get message details."""
        url = f"{self.base_url}/v2/users/{self.email_account}/messages/{message_id}"
        response = await self._request("GET", url)
        return response.json()

    async def list_attachments(self, message_id: str) -> list[dict[str, Any]]:
        """List message attachments."""
        url = f"{self.base_url}/v2/users/{self.email_account}/messages/{message_id}/attachments"
        response = await self._request("GET", url)
        data = response.json()
        return data.get("attachments", [])

    async def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download attachment (streaming download)."""
        url = f"{self.base_url}/v2/users/{self.email_account}/messages/{message_id}/attachments/{attachment_id}/$value"
        response = await self._request("GET", url, retry_on_auth_error=True)
        return response.content

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
