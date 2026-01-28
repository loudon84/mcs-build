"""Base processor interface."""

from abc import ABC, abstractmethod

from mcs_contracts import EmailEvent


class BaseProcessor(ABC):
    """Base interface for message processors."""

    @abstractmethod
    def parse_to_event(self, message_data: dict) -> EmailEvent:
        """Parse channel-specific message data to EmailEvent."""
        pass

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """Return channel type identifier."""
        pass

