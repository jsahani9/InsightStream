"""
Full pipeline integration test.

Runs all 10 agents/services in sequence without LangGraph,
manually threading state through each step.
Prints DB state at key checkpoints so you can verify updates.

Usage:
    1. Run migrations:      alembic upgrade head
    2. Create test user:    python seed_db.py
    3. Paste user_id below: USER_ID / USER_EMAIL
    4. Run this script:     python test_pipeline.py
"""

import asyncio
import json
import logging
import uuid

from sqlalchemy import select

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

# ── CONFIG — paste values from seed_db.py output ──────────────────────────
USER_ID    = "416039ba-61a1-4960-ac38-1d9ef4acf080"
USER_EMAIL = "akash7@my.yorku.ca"
RAW_PREFS  = "I'm interested in AI and FinTech news. Exclude crypto. Send me 5 articles a day."
# ──────────────────────────────────────────────────────────────────────────

from core.config import settings
from db.models import Preference, User
from db import session as db_session
from db.session import init_db
from agents import (
    classifier_agent,
    planner_agent,
    preference_extraction_agent,
    ranking_agent,
    summarization_agent,
    verification_agent,
)
from services import article_fetcher, deduplication, digest_composition, email_delivery


def sep(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


async def check_db_preferences(user_id: str) -> None:
    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(
            select(Preference).where(Preference.user_id == uuid.UUID(user_id))
        )
        pref = result.scalar_one_or_none()
        if pref:
            print(f"  DB preferences row: FOUND")
            print(f"    interests      : {pref.interests}")
            print(f"    excluded_topics: {pref.excluded_topics}")
            print(f"    article_count  : {pref.article_count}")
            print(f"    updated_at     : {pref.updated_at}")
        else:
            print(f"  DB preferences row: NOT FOUND")


async def check_db_user(user_id: str) -> None:
    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user:
            print(f"  DB user row: FOUND — email={user.email}, subscribed={user.is_subscribed}")
        else:
            print(f"  DB user row: NOT FOUND")


async def main() -> None:

    # ── 0. Init DB ─────────────────────────────────────────────────────
    sep("0. Init DB")
    init_db(settings.database_url)
    print("  DB initialized")
    await check_db_user(USER_ID)

    state: dict = {
        "user_id": USER_ID,
        "user_email": USER_EMAIL,
        "raw_preferences": {"user_id": USER_ID, "text": RAW_PREFS},
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

    # ── 1. Preference Extraction ────────────────────────────────────────
    sep("1. Preference Extraction Agent")
    structured = await preference_extraction_agent.run(
        {"user_id": USER_ID, "text": RAW_PREFS}
    )
    state["structured_preferences"] = structured
    print(f"  Extracted: {json.dumps(structured, indent=4)}")
    print()
    await check_db_preferences(USER_ID)

    # ── 2. Planner ──────────────────────────────────────────────────────
    sep("2. Planner Agent")
    planner_out = await planner_agent.run(state)
    state.update(planner_out)
    fetch_plan   = state["fetch_plan"]
    web_articles = state["raw_articles"]
    sources = fetch_plan.get("sources", [])
    print(f"  Sources from plan ({len(sources)}):")
    for s in sources:
        print(f"    {s}")
    print(f"  Category weights: {fetch_plan.get('category_weights', {})}")
    print(f"  Web articles (from search): {len(web_articles)}")

    # ── 3. Fetch RSS Articles ───────────────────────────────────────────
    sep("3. Article Fetcher (RSS)")
    rss_articles = article_fetcher.fetch(sources) if sources else []
    print(f"  RSS articles fetched: {len(rss_articles)}")
    all_articles = web_articles + rss_articles
    state["raw_articles"] = all_articles
    print(f"  Total raw articles (web + RSS): {len(all_articles)}")

    # ── 4. Classifier ───────────────────────────────────────────────────
    sep("4. Classifier Agent")
    classifier_out = classifier_agent.run(state)
    state.update(classifier_out)
    classified = state["classified_articles"]
    counts: dict[str, int] = {}
    for a in classified:
        cat = a.get("category", "?")
        counts[cat] = counts.get(cat, 0) + 1
    print(f"  Classified {len(classified)} articles: {counts}")

    # ── 5. Deduplication ────────────────────────────────────────────────
    sep("5. Deduplication Service")
    deduped = await deduplication.deduplicate(classified, USER_ID)
    state["deduplicated_articles"] = deduped
    print(f"  {len(classified)} → {len(deduped)} articles after dedup")

    # ── 6. Ranking ──────────────────────────────────────────────────────
    sep("6. Ranking Agent")
    ranking_out = ranking_agent.run(state)
    state.update(ranking_out)
    ranked = state["ranked_articles"]
    print(f"  Top {len(ranked)} articles:")
    for a in ranked:
        print(f"    [{a.get('score', '?'):>3}] {a.get('title', '')[:65]}")

    # ── 6.5. Content Enrichment ─────────────────────────────────────────
    sep("6.5. Content Enrichment (fetch full article text)")
    enriched_ranked = article_fetcher.enrich_with_content(ranked)
    state["ranked_articles"] = enriched_ranked
    print(f"  Fetched full content for {len(enriched_ranked)} articles")

    # ── 7. Summarization ────────────────────────────────────────────────
    sep("7. Summarization Agent")
    summ_out = summarization_agent.run(state)
    state.update(summ_out)
    summaries = state["summaries"]
    print(f"  Summaries generated: {len(summaries)}")
    if summaries:
        s = summaries[0]
        print(f"\n  Sample summary — {s['title'][:65]}")
        for b in s.get("bullets", []):
            print(f"    • {b}")
        wim = s.get("why_it_matters", "")
        if wim:
            print(f"    Why it matters: {wim[:120]}")

    # ── 8. Verification ─────────────────────────────────────────────────
    sep("8. Verification Agent")
    verif_out = verification_agent.run(state)
    state.update(verif_out)
    verified = state["verified_summaries"]
    print(f"  {len(verified)}/{len(summaries)} summaries passed verification")

    # ── 9. Digest Composition ───────────────────────────────────────────
    sep("9. Digest Composition")
    digest = digest_composition.compose(verified, state["structured_preferences"])
    state["digest"] = digest
    print(f"  HTML digest length: {len(digest)} chars")
    print(f"  Stories included  : {len(verified)}")

    # ── 10. Email Delivery ──────────────────────────────────────────────
    sep("10. Email Delivery")
    await email_delivery.send(USER_ID, USER_EMAIL, digest)
    print(f"  Email sent to {USER_EMAIL}")

    # ── Final DB check ──────────────────────────────────────────────────
    sep("Final DB State")
    await check_db_user(USER_ID)
    await check_db_preferences(USER_ID)

    sep("DONE — full pipeline completed")


asyncio.run(main())
