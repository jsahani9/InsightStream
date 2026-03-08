"""Digest composition service.

Assembles verified summaries into a structured, email-ready digest.
"""


def compose(verified_summaries: list[dict], user_preferences: dict) -> str:
    """Build the final digest string from verified summaries."""
    raise NotImplementedError
