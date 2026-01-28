"""Base listener interface for communication channels."""

from abc import ABC, abstractmethod
from typing import Any


class BaseListener(ABC):
    """Base interface for all communication channel listeners."""

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the communication channel."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the communication channel."""
        pass

    @abstractmethod
    async def poll_new_messages(self, **kwargs) -> list[str]:
        """Poll for new messages, return list of message IDs/UIDs."""
        pass

    @abstractmethod
    async def fetch_message(self, message_id: str) -> dict[str, Any]:
        """Fetch message content by ID."""
        pass

    @abstractmethod
    async def mark_as_processed(self, message_id: str) -> None:
        """Mark message as processed."""
        pass

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """Return channel type identifier (e.g., 'email', 'wechat')."""
        pass

