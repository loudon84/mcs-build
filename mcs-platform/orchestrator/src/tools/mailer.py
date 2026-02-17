"""Email sending tools."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from observability.logging import get_logger
from settings import Settings

logger = get_logger()


class Mailer:
    """Email sender using SMTP."""

    def __init__(self, settings: Settings):
        """Initialize mailer."""
        self.settings = settings
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
        )

    def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        cc: Optional[list[str]] = None,
    ) -> Optional[str]:
        """Send email via SMTP."""
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.settings.smtp_user
            msg["To"] = ", ".join(to) if isinstance(to, list) else to
            if cc:
                msg["Cc"] = ", ".join(cc)
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                server.starttls()
                server.login(self.settings.smtp_user, self.settings.smtp_pass)
                recipients = (to if isinstance(to, list) else [to]) + (cc or [])
                server.send_message(msg, to_addrs=recipients)

            return msg["Message-ID"]
        except Exception as e:
            logger.error(
                "Failed to send email",
                extra={
                    "to": to,
                    "subject": subject,
                },
                exc_info=True,
            )
            return None

    def render_template(self, template_name: str, **kwargs) -> str:
        """Render email template."""
        template = self.jinja_env.get_template(template_name)
        return template.render(**kwargs)

