"""Listener service for message listening and polling."""

from typing import Optional

from mcs_contracts import EmailEvent
from listener.processors.email import EmailProcessor
from listener.processors.wechat import WeChatProcessor
from listener.repo import ListenerRepo
from listener.scheduler import UnifiedScheduler
from services.orchestration_service import OrchestrationService
from settings import Settings


class ListenerService:
    """Service for listener operations."""

    def __init__(
        self,
        settings: Settings,
        repo: Optional[ListenerRepo] = None,
        orchestration_service: Optional[OrchestrationService] = None,
    ):
        """Initialize listener service."""
        self.settings = settings
        self.repo = repo
        self.orchestration_service = orchestration_service
        self.scheduler: Optional[UnifiedScheduler] = None

    async def start_scheduler(self) -> None:
        """Start scheduler for all enabled listeners."""
        if self.scheduler:
            return

        self.scheduler = UnifiedScheduler(self.settings, self.repo)
        if self.orchestration_service:
            self.scheduler.set_orchestration_service(self.orchestration_service)
        await self.scheduler.start()

    async def stop_scheduler(self) -> None:
        """Stop scheduler and disconnect all listeners."""
        if self.scheduler:
            await self.scheduler.stop()
            self.scheduler = None

    async def trigger_poll(self) -> None:
        """Manually trigger polling for all enabled listeners."""
        if not self.scheduler:
            await self.start_scheduler()

        # Poll all channels
        if "email" in self.settings.get_enabled_listeners():
            await self.scheduler._poll_email()
        if "wechat" in self.settings.get_enabled_listeners():
            await self.scheduler._poll_wechat()

    async def handle_webhook_email(self, email_data: dict) -> None:
        """Handle email webhook (e.g., from Exchange)."""
        processor = EmailProcessor()
        email_event = processor.parse_to_event(email_data)
        
        if self.orchestration_service:
            await self.orchestration_service.run_sales_email(email_event)
        else:
            raise RuntimeError("OrchestrationService not set in ListenerService")

    async def handle_webhook_wechat(self, wechat_data: dict) -> None:
        """Handle WeChat webhook."""
        processor = WeChatProcessor()
        email_event = processor.parse_to_event(wechat_data)
        
        if self.orchestration_service:
            await self.orchestration_service.run_sales_email(email_event)
        else:
            raise RuntimeError("OrchestrationService not set in ListenerService")

    def get_status(self) -> dict:
        """Get service status."""
        return {
            "status": "ok",
            "service": "orchestrator-listener",
            "enabled_channels": self.settings.get_enabled_listeners(),
            "scheduler_running": self.scheduler is not None,
        }
