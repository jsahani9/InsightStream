"""Email delivery service.

Sends the composed digest to the user via SMTP using aiosmtplib.
Checks subscription status before sending — unsubscribed users are silently skipped. ---- 

New Stuff :
    - Subscription Check
    - Unsubscribed user won't receive the mail


"""


import logging
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from core.config import settings
from tools.database_query_tool import is_user_subscribed

logger = logging.getLogger(__name__)

# macOS fix: system CA certs not loaded by default in Python
_ssl_context = ssl.create_default_context()


async def send(user_id: str, user_email: str, digest: str) -> None:
    """Send the HTML digest email to the given address.

    Checks subscription status first — if the user has unsubscribed,
    the email is silently skipped and no exception is raised.

    Args:
        user_id:    UUID string of the user (used for subscription check).
        user_email: Recipient email address.
        digest:     HTML digest string to send.
    """
    subscribed = await is_user_subscribed(user_id)
    if not subscribed:
        logger.info(
            "Skipping digest for user %s (%s) — not subscribed.", user_id, user_email
        )
        return

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

    logger.info("Digest sent to %s (user %s)", user_email, user_id)
