"""Message processors for different channels."""

from processors.base import BaseProcessor
from processors.email import EmailProcessor
from processors.wechat import WeChatProcessor

__all__ = ["BaseProcessor", "EmailProcessor", "WeChatProcessor"]

