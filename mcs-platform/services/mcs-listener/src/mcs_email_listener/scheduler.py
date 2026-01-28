"""Email polling scheduler."""

import asyncio
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from mcs_email_listener.fetcher import parse_email_to_event, trigger_orchestrator
from mcs_email_listener.listeners.imap_listener import IMAPListener
from mcs_email_listener.settings import Settings


class EmailScheduler:
    """Email polling scheduler."""

    def __init__(self, settings: Settings):
        """Initialize scheduler."""
        self.settings = settings
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.listener: Optional[IMAPListener] = None

    async def start(self) -> None:
        """Start scheduler."""
        self.scheduler = AsyncIOScheduler()
        self.listener = IMAPListener(
            host=self.settings.imap_host,
            port=self.settings.imap_port,
            user=self.settings.imap_user,
            password=self.settings.imap_pass,
        )

        # Schedule polling job
        self.scheduler.add_job(
            self._poll_emails,
            trigger=IntervalTrigger(seconds=self.settings.poll_interval_seconds),
            id="poll_emails",
            replace_existing=True,
        )

        self.scheduler.start()

    async def _poll_emails(self) -> None:
        """Poll emails and trigger orchestrator."""
        try:
            self.listener.connect()
            uids = self.listener.poll_new_emails()

            for uid in uids:
                try:
                    email_data = self.listener.fetch_email(uid)
                    email_event = parse_email_to_event(
                        email_data,
                        provider=self.settings.email_provider,
                        account=self.settings.imap_user,
                    )

                    # Trigger orchestrator
                    await trigger_orchestrator(email_event, self.settings)

                    # Mark as read
                    self.listener.mark_as_read(uid)
                except Exception as e:
                    print(f"Failed to process email {uid}: {e}")

        except Exception as e:
            print(f"Failed to poll emails: {e}")
        finally:
            if self.listener:
                self.listener.disconnect()

    async def stop(self) -> None:
        """Stop scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
        if self.listener:
            self.listener.disconnect()

