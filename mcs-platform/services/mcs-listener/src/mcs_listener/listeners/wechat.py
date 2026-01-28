"""WeChat Work (企业微信) listener implementation."""

from typing import Any

from mcs_listener.listeners.base import BaseListener


class WeChatListener(BaseListener):
    """WeChat Work listener for enterprise WeChat messages."""

    def __init__(
        self,
        corp_id: str = "",
        corp_secret: str = "",
        agent_id: str = "",
        webhook_url: str = "",
    ):
        """Initialize WeChat listener."""
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.agent_id = agent_id
        self.webhook_url = webhook_url
        self.access_token: str | None = None

    @property
    def channel_type(self) -> str:
        """Return channel type."""
        return "wechat"

    async def connect(self) -> None:
        """Connect to WeChat API and get access token."""
        # TODO: Implement WeChat API authentication
        # This would call WeChat API to get access_token
        raise NotImplementedError("WeChat listener not yet fully implemented")

    async def disconnect(self) -> None:
        """Disconnect from WeChat API."""
        self.access_token = None

    async def poll_new_messages(self, **kwargs) -> list[str]:
        """Poll for new WeChat messages."""
        # TODO: Implement WeChat message polling
        # This would call WeChat API to get new messages
        raise NotImplementedError("WeChat message polling not yet implemented")

    async def fetch_message(self, message_id: str) -> dict[str, Any]:
        """Fetch WeChat message content."""
        # TODO: Implement WeChat message fetching
        # This would call WeChat API to get message details
        raise NotImplementedError("WeChat message fetching not yet implemented")

    async def mark_as_processed(self, message_id: str) -> None:
        """Mark WeChat message as processed."""
        # TODO: Implement WeChat message marking
        raise NotImplementedError("WeChat message marking not yet implemented")

    async def _get_access_token(self) -> str:
        """Get WeChat API access token."""
        # TODO: Implement token refresh logic
        if not self.access_token:
            # Call WeChat API to get token
            pass
        return self.access_token or ""

