"""InsightStream Scheduler

Runs the digest pipeline for ALL subscribed users every day at 9:00 AM.

Usage:
    python scheduler.py

Keep this running in the background (e.g. via screen/tmux or a systemd service).
It will fire at 9am daily and send each subscribed user their digest.
"""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from core.config import settings
from db import session as db_session
from db.models import User

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
log = logging.getLogger(__name__)


async def run_digest_for_user(user_id: str, user_email: str) -> None:
    """Run the full pipeline for a single user and send their digest."""
    log.info(f"Running digest for {user_email} ...")
    try:
        from graph.pipeline import build_pipeline

        pipeline = build_pipeline()
        initial_state = {
            "user_id": user_id,
            "user_email": user_email,
            "raw_preferences": {},
            "structured_preferences": {},
            "fetch_plan": {},
            "raw_articles": [],
            "classified_articles": [],
            "deduplicated_articles": [],
            "ranked_articles": [],
            "summaries": [],
            "verified_summaries": [],
            "digest": "",
        }
        await pipeline.ainvoke(initial_state)
        log.info(f"Digest sent to {user_email}")
    except Exception as e:
        log.error(f"Failed for {user_email}: {e}")


async def run_all_digests() -> None:
    """Fetch all subscribed users and run the pipeline for each."""
    log.info("=== Daily digest job started ===")

    async with db_session.AsyncSessionLocal() as s:
        result = await s.execute(
            select(User).where(User.is_subscribed == True)  # noqa: E712
        )
        users = result.scalars().all()

    if not users:
        log.info("No subscribed users found — nothing to do.")
        return

    log.info(f"Found {len(users)} subscribed user(s). Sending digests...")

    for user in users:
        await run_digest_for_user(str(user.id), user.email)

    log.info("=== Daily digest job complete ===")


async def main():
    db_session.init_db(settings.database_url)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_all_digests,
        trigger=CronTrigger(hour=9, minute=0),   # 9:00 AM every day
        id="daily_digest",
        name="Daily digest for all subscribed users",
        replace_existing=True,
    )

    scheduler.start()
    log.info("Scheduler started. Digests will run daily at 9:00 AM.")
    log.info("Press Ctrl+C to stop.")

    try:
        # Keep the event loop alive
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    asyncio.run(main())
