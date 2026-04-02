"""Database Query Tool.

Exposes safe, scoped database functions to agents.
Agents never execute raw SQL — only call these functions.

-- Each Function opens and closes it's own session, they are stateless and safe to call from any agent

"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from db.models import Preference, SentArticle, User # Use database file and call out the functions
from db import session as db_session   # can always see the initialised value after init_db() is called


async def get_user_preferences(user_id: str) -> dict:
    """Return the structured preference profile for a user.
    - A plain dict with interests, excluded_topics, article_count and extra

    Returns an empty dict if no preference row exists yet.
    """
    if db_session.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    uid = uuid.UUID(user_id)

    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(
            select(Preference).where(Preference.user_id == uid)
        )
        pref = result.scalar_one_or_none()

    if pref is None:
        return {}

    return {
        "user_id": str(pref.user_id),
        "interests": pref.interests,
        "categories": (pref.extra or {}).get("categories", []),
        "excluded_topics": pref.excluded_topics,
        "article_count": pref.article_count,
        "extra": pref.extra,
        "updated_at": pref.updated_at.isoformat(),
    }


async def get_recently_sent_articles(user_id: str, days: int = 7) -> list[str]:
    """Return article IDs delivered to a user in the last N days.
    Used by the deduplication service to avoid re-sending articles the user already received
    """
    if db_session.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    uid = uuid.UUID(user_id)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(
            select(SentArticle.article_id).where(
                SentArticle.user_id == uid,
                SentArticle.sent_at >= cutoff,
            )
        )
        rows = result.scalars().all()

    return [str(article_id) for article_id in rows]


async def is_user_subscribed(user_id: str) -> bool:
    """Return True if the user is currently subscribed to digest delivery."""
    if db_session.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    uid = uuid.UUID(user_id)

    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.is_subscribed).where(User.id == uid)
        )
        subscribed = result.scalar_one_or_none()

    if subscribed is None:
        return False

    return bool(subscribed)
