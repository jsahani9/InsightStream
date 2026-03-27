"""Email delivery service.

Sends the composed digest to the user via SMTP using aiosmtplib.
"""

import logging
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from core.config import settings

logger = logging.getLogger(__name__)

# macOS fix: system CA certs not loaded by default in Python
_ssl_context = ssl.create_default_context()


async def send(user_email: str, digest: str) -> None:
    """Send the HTML digest email to the given address."""
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"InsightStream Digest — {today}"
    msg["From"] = settings.email_from
    msg["To"] = user_email

    msg.attach(MIMEText(digest, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        start_tls=True,
        tls_context=_ssl_context,
    )

    logger.info("Digest sent to %s", user_email)
