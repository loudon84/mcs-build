"""Email listener implementation."""

import email
import email.utils
import imaplib
from typing import Any, Optional

from listener.listeners.base import BaseListener


class EmailListener(BaseListener):
    """Email listener for IMAP/Exchange/POP3."""

    def __init__(
        self,
        provider: str = "imap",
        host: str = "",
        port: int = 993,
        user: str = "",
        password: str = "",
        exchange_tenant_id: str = "",
        exchange_client_id: str = "",
        exchange_client_secret: str = "",
    ):
        """Initialize email listener."""
        self.provider = provider
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.exchange_tenant_id = exchange_tenant_id
        self.exchange_client_id = exchange_client_id
        self.exchange_client_secret = exchange_client_secret
        self.connection: Optional[imaplib.IMAP4_SSL] = None

    @property
    def channel_type(self) -> str:
        """Return channel type."""
        return "email"

    async def connect(self) -> None:
        """Connect to email server.
        
        Note: For Alibaba Mail (imap.qiye.aliyun.com), you must use an 
        application password (三方客户端安全密码), not the regular email password.
        Get it from: 邮箱设置 → 账户与安全 → 三方客户端安全密码
        """
        if self.provider == "imap":
            try:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
                self.connection.login(self.user, self.password)
            except imaplib.IMAP4.error as e:
                error_msg = str(e)
                # 提供更详细的错误信息，特别是针对阿里企业邮箱
                if "LOGIN failed" in error_msg or "AUTHENTICATE failed" in error_msg:
                    hint = ""
                    if "qiye.aliyun.com" in self.host or "aliyun.com" in self.host:
                        hint = (
                            "\n提示：阿里企业邮箱需要使用'三方客户端安全密码'（应用密码），"
                            "而不是邮箱登录密码。\n"
                            "获取方式：登录邮箱 → 设置 → 账户与安全 → 三方客户端安全密码 → 生成新密码\n"
                            "如果已生成但仍失败，请检查：\n"
                            "1. 管理员是否在域管后台禁用了'禁止使用三方客户端'\n"
                            "2. 账号的 POP/IMAP/SMTP 功能是否已开启\n"
                            "3. 是否多次输错密码导致账号被锁定（通常1小时后自动解锁）"
                        )
                    else:
                        hint = (
                            "\n提示：请检查：\n"
                            "1. 用户名和密码是否正确\n"
                            "2. 是否启用了 IMAP 服务\n"
                            "3. 是否需要使用应用密码（授权码）而非登录密码\n"
                            "4. 账号是否被锁定"
                        )
                    raise ConnectionError(
                        f"Failed to connect to IMAP server: {error_msg}{hint}"
                    ) from e
                else:
                    raise ConnectionError(f"Failed to connect to IMAP server: {error_msg}") from e
            except Exception as e:
                raise ConnectionError(f"Failed to connect to IMAP server: {str(e)}") from e
        elif self.provider == "exchange":
            # TODO: Implement Exchange connection
            raise NotImplementedError("Exchange provider not yet implemented")
        elif self.provider == "pop3":
            # TODO: Implement POP3 connection
            raise NotImplementedError("POP3 provider not yet implemented")
        else:
            raise ValueError(f"Unsupported email provider: {self.provider}")

    async def disconnect(self) -> None:
        """Disconnect from email server."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except Exception:
                pass
            finally:
                self.connection = None

    async def poll_new_messages(self, folder: str = "INBOX") -> list[str]:
        """Poll for new emails."""
        if not self.connection:
            await self.connect()

        if self.provider == "imap":
            self.connection.select(folder)
            _, message_numbers = self.connection.search(None, "UNSEEN")
            return message_numbers[0].split() if message_numbers[0] else []
        else:
            raise NotImplementedError(f"Polling not implemented for provider: {self.provider}")

    async def fetch_message(self, uid: str) -> dict[str, Any]:
        """Fetch email content."""
        if not self.connection:
            await self.connect()

        if self.provider == "imap":
            _, msg_data = self.connection.fetch(uid, "(RFC822)")
            email_body = msg_data[0][1]
            msg = email.message_from_bytes(email_body)

            return {
                "uid": uid,
                "message_id": msg.get("Message-ID", ""),
                "from": msg.get("From", ""),
                "to": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "body": self._get_body(msg),
                "attachments": self._get_attachments(msg),
                "received_at": self._get_received_at(msg),
                "provider": self.provider,
                "account": self.user,
            }
        else:
            raise NotImplementedError(f"Fetch not implemented for provider: {self.provider}")

    async def mark_as_processed(self, uid: str) -> None:
        """Mark email as read."""
        if not self.connection:
            return

        if self.provider == "imap":
            self.connection.store(uid, "+FLAGS", "\\Seen")
        else:
            raise NotImplementedError(f"Mark as processed not implemented for provider: {self.provider}")

    def _get_received_at(self, msg: email.message.Message) -> str:
        """Extract received time from the first Received header (RFC 5322)."""
        received = msg.get("Received")
        if not received:
            return ""
        parts = received.rsplit(";", 1)
        date_str = parts[-1].strip() if len(parts) > 1 else received.strip()
        if not date_str:
            return ""
        try:
            dt = email.utils.parsedate_to_datetime(date_str)
            return dt.isoformat()
        except (ValueError, TypeError):
            return ""

    def _get_body(self, msg: email.message.Message) -> str:
        """Extract email body."""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        return body

    def _get_attachments(self, msg: email.message.Message) -> list[dict[str, Any]]:
        """Extract email attachments."""
        attachments = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            "filename": filename,
                            "content_type": part.get_content_type(),
                            "payload": part.get_payload(decode=True),
                        })
        return attachments
