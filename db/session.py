"""Database session management.

Provides an async SQLAlchemy engine and session factory.
"""

from collections.abc import AsyncGenerator
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = None          # initialized from config.DATABASE_URL at startup
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def _prepare_url(database_url: str) -> tuple[str, dict]:
    """Strip libpq-only query params and return (clean_url, connect_args).

    asyncpg does not accept sslmode or channel_binding as URL query params;
    SSL must be passed via connect_args instead.
    """
    parsed = urlparse(database_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    ssl_modes = {"require", "verify-ca", "verify-full"}
    use_ssl = params.pop("sslmode", ["disable"])[0] in ssl_modes
    params.pop("channel_binding", None)

    clean_query = urlencode({k: v[0] for k, v in params.items()})
    clean_url = urlunparse(parsed._replace(query=clean_query))

    connect_args: dict = {"ssl": True} if use_ssl else {}
    return clean_url, connect_args


def init_db(database_url: str) -> None:
    """Initialize the async engine and session factory."""
    global engine, AsyncSessionLocal
    clean_url, connect_args = _prepare_url(database_url)
    engine = create_async_engine(clean_url, connect_args=connect_args, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session (for use as a FastAPI dependency)."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with AsyncSessionLocal() as session:
        yield session
