"""
Seed script — creates a test user in the database.

Run this once before test_pipeline.py:
    python seed_db.py

It prints the user_id and email — paste them into test_pipeline.py.
"""

import asyncio
import uuid

from sqlalchemy import select

from core.config import settings
from db.models import User
from db import session as db_session
from db.session import init_db

TEST_EMAIL = "akash7@my.yorku.ca"


async def seed():
    init_db(settings.database_url)

    async with db_session.AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(select(User).where(User.email == TEST_EMAIL))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"User already exists:")
            print(f"  user_id : {existing.id}")
            print(f"  email   : {existing.email}")
            print(f"  subscribed: {existing.is_subscribed}")
            return

        user = User(
            id=uuid.uuid4(),
            email=TEST_EMAIL,
            is_subscribed=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        print(f"Created test user:")
        print(f"  user_id : {user.id}")
        print(f"  email   : {user.email}")
        print(f"  subscribed: {user.is_subscribed}")
        print()
        print("Paste these into test_pipeline.py:")
        print(f'  USER_ID    = "{user.id}"')
        print(f'  USER_EMAIL = "{user.email}"')


asyncio.run(seed())
