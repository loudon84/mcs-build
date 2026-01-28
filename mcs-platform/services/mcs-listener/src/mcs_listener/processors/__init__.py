"""Message processors for different channels."""

from mcs_listener.processors.base import BaseProcessor
from mcs_listener.processors.email import EmailProcessor
from mcs_listener.processors.wechat import WeChatProcessor

__all__ = ["BaseProcessor", "EmailProcessor", "WeChatProcessor"]

