"""

SQLAlchemy ORM models.

Tables:
- users           — registered users and their subscription status
- preferences     — structured user preference profiles
- articles        — ingested and processed articles
- sent_articles   — delivery history per user
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Model classes will be defined here (User, Preference, Article, SentArticle)
