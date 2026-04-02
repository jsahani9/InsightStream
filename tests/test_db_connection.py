import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text

from db import session as db_session

load_dotenv()

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL is not set in .env")


async def main() -> None:
    db_session.init_db(DATABASE_URL)

    if db_session.AsyncSessionLocal is None:
        raise RuntimeError("Database session factory was not initialized.")

    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        value = result.scalar_one_or_none()
        print(f"Database connectivity check result: {value}")


if __name__ == "__main__":
    asyncio.run(main())

