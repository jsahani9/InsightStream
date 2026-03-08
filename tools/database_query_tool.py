"""Database Query Tool.

Exposes safe, scoped database functions to agents.
Agents never execute raw SQL — only call these functions.
"""


def get_user_preferences(user_id: str) -> dict:
    """Return the structured preference profile for a user."""
    raise NotImplementedError


def get_recently_sent_articles(user_id: str, days: int = 7) -> list[str]:
    """Return article IDs delivered to a user in the last N days."""
    raise NotImplementedError


def is_user_subscribed(user_id: str) -> bool:
    """Return True if the user is currently subscribed to digest delivery."""
    raise NotImplementedError
