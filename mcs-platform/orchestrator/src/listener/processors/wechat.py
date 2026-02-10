"""WeChat message processor."""

from mcs_contracts import EmailEvent, now_iso
from listener.processors.base import BaseProcessor


class WeChatProcessor(BaseProcessor):
    """WeChat message processor."""

    @property
    def channel_type(self) -> str:
        """Return channel type."""
        return "wechat"

    def parse_to_event(self, message_data: dict) -> EmailEvent:
        """Parse WeChat message data to EmailEvent."""
        # TODO: Implement WeChat message parsing
        # WeChat messages may have different structure
        # For now, convert to EmailEvent format for compatibility

        # Extract attachments from WeChat message
        attachments = []
        # TODO: Parse WeChat attachments

        return EmailEvent(
            provider="wechat_work",
            account=message_data.get("corp_id", ""),
            folder="chat",
            uid=message_data.get("msgid", ""),
            message_id=message_data.get("msgid", ""),
            from_email=message_data.get("from_userid", ""),
            to=[message_data.get("to_userid", "")],
            cc=[],
            subject="",  # WeChat messages typically don't have subjects
            body_text=message_data.get("content", ""),
            received_at=now_iso(),
            attachments=attachments,
        )
