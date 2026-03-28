"""SQLAlchemy ORM models.

Tables:
- users           — registered users and their subscription status
- preferences     — structured user preference profiles
- articles        — ingested and processed articles
- sent_articles   — delivery history per user
"""

import uuid   # Generate a unique number 
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)


from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(timezone.utc)

# DeclarativeBase sets up the infrastructure for defining database models.
class Base(DeclarativeBase):
    pass


class User(Base):
    """ Registered users and their subscription status. """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    is_subscribed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    preference: Mapped["Preference | None"] = relationship(
        "Preference", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sent_articles: Mapped[list["SentArticle"]] = relationship(
        "SentArticle", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


# Mapper : In SQLAlchemy handles mapping between python classes and database tables
# Convert python objects into database columns 



class Preference(Base):
    """Structured user preference profile extracted by the Preference Extraction Agent."""

    __tablename__ = "preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    interests: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    excluded_topics: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, default=list
    )
    article_count: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    extra: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    user: Mapped["User"] = relationship("User", back_populates="preference")

    def __repr__(self) -> str:
        return f"<Preference user_id={self.user_id} interests={self.interests}>"


class Article(Base):
    """Ingested and processed articles fetched from RSS / web sources."""

    __tablename__ = "articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )

    sent_records: Mapped[list["SentArticle"]] = relationship(
        "SentArticle", back_populates="article", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Article id={self.id} title={self.title!r}>"


class SentArticle(Base):
    """Delivery history — tracks which articles were sent to which user."""

    __tablename__ = "sent_articles"
    __table_args__ = (
        UniqueConstraint("user_id", "article_id", name="uq_sent_user_article"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, index=True
    )

    user: Mapped["User"] = relationship("User", back_populates="sent_articles")
    article: Mapped["Article"] = relationship("Article", back_populates="sent_records")

    def __repr__(self) -> str:
        return f"<SentArticle user_id={self.user_id} article_id={self.article_id}>"
