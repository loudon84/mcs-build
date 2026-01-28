"""Unified scheduler for all communication channels."""

import asyncio
from typing import Optional
from uuid import uuid4

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db.repo import ListenerRepo
from listeners.email import EmailListener
from listeners.wechat import WeChatListener
from orchestrator_client import trigger_orchestrator
from processors.email import EmailProcessor
from processors.wechat import WeChatProcessor
from settings import Settings


class UnifiedScheduler:
    """Unified scheduler for multiple communication channels."""

    def __init__(self, settings: Settings, repo: Optional[ListenerRepo] = None):
        """Initialize scheduler."""
        self.settings = settings
        self.repo = repo
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.listeners: dict[str, any] = {}
        self.processors: dict[str, any] = {}

    async def start(self) -> None:
        """Start scheduler for all enabled listeners."""
        self.scheduler = AsyncIOScheduler()

        enabled = self.settings.get_enabled_listeners()

        # Initialize email listener
        if "email" in enabled:
            if self.settings.email_provider == "alimail":
                from listeners.alimail_listener import AlimailListener
                
                email_listener = AlimailListener(
                    client_id=self.settings.alimail_client_id,
                    client_secret=self.settings.alimail_client_secret,
                    email_account=self.settings.alimail_email_account,
                    folder_id=self.settings.alimail_folder_id,
                    base_url=self.settings.alimail_api_base_url,
                    poll_size=self.settings.alimail_poll_size,
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
            wechat_listener = WeChatListener(
                corp_id=self.settings.wechat_corp_id,
                corp_secret=self.settings.wechat_corp_secret,
                agent_id=self.settings.wechat_agent_id,
                webhook_url=self.settings.wechat_webhook_url,
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

                    # Check if already processed
                    if self.repo:
                        existing = self.repo.find_message_by_id(
                            email_event.message_id, channel_type="email"
                        )
                        if existing and existing.processed:
                            continue

                        # Create record
                        record_id = str(uuid4())
                        self.repo.create_message_record(
                            record_id=record_id,
                            message_id=email_event.message_id,
                            channel_type="email",
                            provider=email_event.provider,
                            account=email_event.account,
                            uid=email_event.uid,
                        )

                    # Trigger orchestrator
                    await trigger_orchestrator(email_event, self.settings)

                    # Mark as processed
                    await listener.mark_as_processed(uid)
                    if self.repo and record_id:
                        self.repo.mark_as_processed(record_id)

                except Exception as e:
                    print(f"Failed to process email {uid}: {e}")

        except Exception as e:
            print(f"Failed to poll emails: {e}")
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
                        )

                    # Trigger orchestrator
                    await trigger_orchestrator(email_event, self.settings)

                    # Mark as processed
                    await listener.mark_as_processed(msg_id)
                    if self.repo and record_id:
                        self.repo.mark_as_processed(record_id)

                except Exception as e:
                    print(f"Failed to process WeChat message {msg_id}: {e}")

        except Exception as e:
            print(f"Failed to poll WeChat messages: {e}")
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

