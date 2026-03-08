"""Email delivery service.

Sends the composed digest to the user via SMTP.
Checks subscription status before sending.
"""


async def send(user_email: str, digest: str) -> None:
    """Send the digest email to the given address."""
    raise NotImplementedError
