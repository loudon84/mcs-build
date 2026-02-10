"""Alimail REST API client."""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from listener.clients.exceptions import AlimailAuthError, AlimailAPIError, AlimailClientError


class OAuthManager:
    """OAuth 2.0 token manager with caching and auto-refresh.

    Token 接口仅支持官方文档中的三个参数：grant_type, client_id, client_secret。
    若返回 1003（请求参数异常），请检查：1）应用是否已绑定/授权目标邮箱；
    2）client_secret 是否含特殊字符（已做 URL 编码）；3）应用是否已启用。
    """

    def __init__(self, client_id: str, client_secret: str, base_url: str = "https://alimail-cn.aliyuncs.com"):
        """Initialize OAuth manager."""
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.base_url = base_url.rstrip("/")
        self.token_url = f"{self.base_url}/oauth2/v2.0/token"
        
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

    def _build_token_body(self) -> bytes:
        """Build application/x-www-form-urlencoded body (only 3 params per Alimail doc).

        Alimail 官方只接受 grant_type, client_id, client_secret；不要传 resource/scope。
        urlencode 会对 client_secret 中的 & = 等做编码，避免参数被截断。
        """
        params = [
            ("grant_type", "client_credentials"),
            ("client_id", self.client_id),
            ("client_secret", self.client_secret),
        ]
        body = urlencode(params)
        return body.encode("utf-8")

    async def refresh_token(self) -> str:
        """Refresh access token."""
        try:
            body = self._build_token_body()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
                    content=body,
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

    def _build_query_str(
        self,
        *,
        keyword: str | None = None,
        from_email: str | None = None,
        folder_id: str | None = None,
        is_read: bool | None = None,
        has_attachments: bool | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> str:
        """Build Alimail queryStr for MailSearchService.SearchMessage.

        Syntax follows official doc:
        https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_message_MailSearchService_SearchMessage
        """
        parts: list[str] = []
        if folder_id is not None:
            parts.append(f"folderId:{folder_id}")
        if is_read is not None:
            parts.append(f"isRead:{str(is_read).lower()}")
        if has_attachments is not None:
            parts.append(f"hasAttachments:{str(has_attachments).lower()}")
        if from_email:
            parts.append(f'from:"{from_email}"')
        if keyword:
            parts.append(f'"{keyword}"')
        if start_time:
            parts.append(f"after:{start_time}")
        if end_time:
            parts.append(f"before:{end_time}")
        return " AND ".join(parts) if parts else "*"

    async def query_messages(
        self,
        body: dict[str, Any] | None = None,
        *,
        keyword: str | None = None,
        from_email: str | None = None,
        folder_id: str | None = None,
        is_read: bool | None = None,
        has_attachments: bool | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        cursor: str = "",
        size: int = 100,
    ) -> dict[str, Any]:
        """Search messages (MailSearchService.SearchMessage).

        API 说明: https://mailhelp.aliyun.com/openapi/index.html#/operations/alimailpb_message_MailSearchService_SearchMessage
        请求体需包含 queryStr（查询表达式），以及分页参数 cursor、size 等，以文档为准。

        Either pass a full request body (body=...) or use keyword args; if both
        are given, body takes precedence.

        Args:
            body: Full request body for the query API (must include queryStr).
                When provided, other keyword args are ignored.
            keyword: Search keyword (subject/body).
            from_email: Filter by sender email.
            folder_id: Restrict search to this folder id.
            is_read: Filter by read state (True=read, False=unread).
            has_attachments: True=with attachments only.
            start_time: Start of time range (ISO8601 or API format).
            end_time: End of time range (ISO8601 or API format).
            cursor: Pagination cursor from previous response.
            size: Page size.

        Returns:
            API response dict (typically contains messages list and next cursor).
        """
        if body is not None:
            payload = body
        else:
            query_str = self._build_query_str(
                keyword=keyword,
                from_email=from_email,
                folder_id=folder_id,
                is_read=is_read,
                has_attachments=has_attachments,
                start_time=start_time,
                end_time=end_time,
            )
            payload = {
                "query": query_str,
                "cursor": cursor,
                "size": size,
            }

        url = f"{self.base_url}/v2/users/{self.email_account}/messages/query?$select=internetMessageId"
        response = await self._request("POST", url, json=payload)
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
