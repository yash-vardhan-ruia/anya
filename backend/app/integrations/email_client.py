"""
CareVoice AI Hospital Platform - SMTP Email Client.

Asynchronous SMTP client using aiosmtplib to send confirmation and receipt emails.
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import aiosmtplib
import structlog
from app.config import settings

logger = structlog.get_logger(__name__)


class EmailClient:
    """Async client wrapper for sending emails via SMTP."""

    def __init__(self) -> None:
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL

        self.configured = bool(self.host and self.username and self.password)
        if not self.configured:
            logger.warning("SMTP credentials not fully configured. Emails will be simulated in logs.")

    async def send_email(self, to_email: str, subject: str, html_content: str) -> None:
        """Send an HTML email asynchronously.

        Args:
            to_email: Recipient's email address
            subject: Email subject line
            html_content: HTML body content of the email
        """
        if not self.configured:
            logger.info("Email simulated (SMTP not configured)", to=to_email, subject=subject, content_preview=html_content[:150])
            return

        try:
            # Construct standard MIME multipart message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject

            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # Determine TLS settings based on standard ports
            use_tls = (self.port == 465)
            
            # Send using aiosmtplib
            smtp_client = aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                use_tls=use_tls,
            )
            
            await smtp_client.connect()
            
            if not use_tls and self.port == 587:
                is_encrypted = False
                if smtp_client.transport is not None and hasattr(smtp_client.transport, "get_extra_info"):
                    ssl_object = smtp_client.transport.get_extra_info("ssl_object")
                    if ssl_object is not None:
                        is_encrypted = True
                if not is_encrypted:
                    await smtp_client.starttls()
                
            await smtp_client.login(self.username, self.password)
            await smtp_client.send_message(msg)
            await smtp_client.quit()
            
            logger.info("Email sent successfully", to=to_email, subject=subject)
        except Exception as e:
            logger.error("Failed to send email", error=str(e), to=to_email, subject=subject)
            # Do not raise error to prevent booking failure if email fails, but log it
            raise RuntimeError(f"Email sending failed: {e}")


# Singleton client instance
email_client = EmailClient()
