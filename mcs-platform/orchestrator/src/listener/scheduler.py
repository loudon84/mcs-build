"""Unified scheduler for all communication channels."""

import asyncio
from typing import Optional
from uuid import uuid4

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from listener.channel.email import EmailListener
from listener.channel.wechat import WeChatListener
from listener.processors.email import EmailProcessor
from listener.processors.wechat import WeChatProcessor
from listener.repo import ListenerRepo
from observability.logging import get_logger
from settings import Settings
from tools.file_server import FileServerClient

logger = get_logger()


class UnifiedScheduler:
    """Unified scheduler for multiple communication channels."""

    def __init__(self, settings: Settings, repo: Optional[ListenerRepo] = None):
        """Initialize scheduler."""
        self.settings = settings
        self.repo = repo
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.listeners: dict[str, any] = {}
        self.processors: dict[str, any] = {}
        self._orchestration_service = None  # Will be injected by ListenerService

    def set_orchestration_service(self, orchestration_service):
        """Set orchestration service for in-process triggering."""
        self._orchestration_service = orchestration_service

    async def start(self) -> None:
        """Start scheduler for all enabled listeners."""
        self.scheduler = AsyncIOScheduler()

        enabled = self.settings.get_enabled_listeners()

        # Initialize email listener
        if "email" in enabled:
            # Get allow list for email channel
            email_allow_list = self.settings.get_channel_allow_list("email")
            
            if self.settings.email_provider == "alimail":
                from listener.channel.alimail import AlimailListener
                
                # Create FileServerClient for attachment saving
                file_client = FileServerClient(
                    base_url=self.settings.file_server_base_url,
                    api_key=self.settings.file_server_api_key,
                )
                
                email_listener = AlimailListener(
                    client_id=self.settings.alimail_client_id,
                    client_secret=self.settings.alimail_client_secret,
                    email_account=self.settings.alimail_email_account,
                    folder_id=self.settings.alimail_folder_id,
                    base_url=self.settings.alimail_api_base_url,
                    poll_size=self.settings.alimail_poll_size,
                    file_client=file_client,
                    repo=self.repo,
                    allow_from=email_allow_list,
                )
            else:
                email_listener = EmailListener(
                    provider=self.settings.email_provider,
                    host=self.settings.imap_host,
                    port=self.settings.imap_port,
                    user=self.settings.imap_user,
                    password=self.settings.imap_pass,
                    exchange_tenant_id=self.settings.exchange_tenant_id,
                    exchange_client_id=self.settings.exchange_client_id,
                    exchange_client_secret=self.settings.exchange_client_secret,
                    allow_from=email_allow_list,
                )
            self.listeners["email"] = email_listener
            self.processors["email"] = EmailProcessor()

            # Schedule email polling
            self.scheduler.add_job(
                self._poll_email,
                trigger=IntervalTrigger(seconds=self.settings.poll_interval_seconds),
                id="poll_email",
                replace_existing=True,
            )

        # Initialize WeChat listener
        if "wechat" in enabled:
            # Get allow list for wechat channel
            wechat_allow_list = self.settings.get_channel_allow_list("wechat")
            
            wechat_listener = WeChatListener(
                corp_id=self.settings.wechat_corp_id,
                corp_secret=self.settings.wechat_corp_secret,
                agent_id=self.settings.wechat_agent_id,
                webhook_url=self.settings.wechat_webhook_url,
                allow_from=wechat_allow_list,
            )
            self.listeners["wechat"] = wechat_listener
            self.processors["wechat"] = WeChatProcessor()

            # Schedule WeChat polling
            self.scheduler.add_job(
                self._poll_wechat,
                trigger=IntervalTrigger(seconds=self.settings.poll_interval_seconds),
                id="poll_wechat",
                replace_existing=True,
            )

        self.scheduler.start()

    async def _poll_email(self) -> None:
        """Poll emails and trigger orchestrator."""
        listener = self.listeners.get("email")
        processor = self.processors.get("email")

        if not listener or not processor:
            return

        try:
            await listener.connect()
            uids = await listener.poll_new_messages()

            for uid in uids:
                record_id = None
                try:
                    message_data = await listener.fetch_message(uid)
                    email_event = processor.parse_to_event(message_data)

                    # Check access control
                    if not listener.is_allowed(email_event.from_email):
                        logger.warning(
                            "Sender not allowed",
                            extra={
                                "from_email": email_event.from_email,
                                "channel": "email",
                                "message_id": email_event.message_id,
                            },
                        )
                        continue

                    # Check if already processed
                    if self.repo:
                        existing = self.repo.find_message_by_id(
                            email_event.message_id, channel_type="email"
                        )
                        if existing and existing.processed:
                            continue

                        # Create record
                        if existing is None:
                            record_id = str(uuid4())
                            self.repo.create_message_record(
                                record_id=record_id,
                                message_id=email_event.message_id,
                                channel_type="email",
                                provider=email_event.provider,
                                account=email_event.account,
                                uid=email_event.uid,
                                from_email=email_event.from_email,
                                received_at=email_event.received_at,
                            )
                        else:
                            record_id = existing.id

                    #没有附件不进行处理
                    if email_event.attachments is None or len(email_event.attachments) <= 0 or (existing and existing.processed):
                        continue

                    # Trigger orchestrator (in-process via OrchestrationService)
                    if self._orchestration_service:
                        await self._orchestration_service.run_sales_email(email_event)
                    else:
                        raise RuntimeError("OrchestrationService not set in scheduler")

                    # Mark as processed
                    await listener.mark_as_processed(uid)
                    if self.repo and record_id:
                        self.repo.mark_as_processed(record_id)

                except Exception as e:
                    logger.error(
                        "Failed to process email",
                        extra={
                            "uid": uid,
                            "message_id": email_event.message_id if "email_event" in locals() else None,
                            "channel": "email",
                        },
                        exc_info=True,
                    )

        except Exception as e:
            logger.error(
                "Failed to poll emails",
                extra={"channel": "email"},
                exc_info=True,
            )
        finally:
            await listener.disconnect()

    async def _poll_wechat(self) -> None:
        """Poll WeChat messages and trigger orchestrator."""
        listener = self.listeners.get("wechat")
        processor = self.processors.get("wechat")

        if not listener or not processor:
            return

        try:
            await listener.connect()
            message_ids = await listener.poll_new_messages()

            for msg_id in message_ids:
                try:
                    message_data = await listener.fetch_message(msg_id)
                    email_event = processor.parse_to_event(message_data)

                    # Check access control
                    sender_id = email_event.from_email  # For wechat, this might be user_id
                    if not listener.is_allowed(sender_id):
                        logger.warning(
                            "Sender not allowed",
                            extra={
                                "sender_id": sender_id,
                                "channel": "wechat",
                                "message_id": email_event.message_id,
                            },
                        )
                        continue

                    # Check if already processed
                    record_id = None
                    if self.repo:
                        existing = self.repo.find_message_by_id(
                            email_event.message_id, channel_type="wechat"
                        )
                        if existing and existing.processed:
                            continue

                        # Create record
                        record_id = str(uuid4())
                        self.repo.create_message_record(
                            record_id=record_id,
                            message_id=email_event.message_id,
                            channel_type="wechat",
                            provider=email_event.provider,
                            account=email_event.account,
                            uid=email_event.uid,
                            from_email=email_event.from_email,
                            received_at=email_event.received_at,
                        )

                    # Trigger orchestrator (in-process via OrchestrationService)
                    if self._orchestration_service:
                        await self._orchestration_service.run_sales_email(email_event)
                    else:
                        raise RuntimeError("OrchestrationService not set in scheduler")

                    # Mark as processed
                    await listener.mark_as_processed(msg_id)
                    if self.repo and record_id:
                        self.repo.mark_as_processed(record_id)

                except Exception as e:
                    logger.error(
                        "Failed to process WeChat message",
                        extra={
                            "msg_id": msg_id,
                            "message_id": email_event.message_id if "email_event" in locals() else None,
                            "channel": "wechat",
                        },
                        exc_info=True,
                    )

        except Exception as e:
            logger.error(
                "Failed to poll WeChat messages",
                extra={"channel": "wechat"},
                exc_info=True,
            )
        finally:
            await listener.disconnect()

    async def stop(self) -> None:
        """Stop scheduler and disconnect all listeners."""
        if self.scheduler:
            self.scheduler.shutdown()

        for listener in self.listeners.values():
            await listener.disconnect()

        self.listeners.clear()
        self.processors.clear()
