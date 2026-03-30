"""End-to-end pipeline test.

Runs the full InsightStream pipeline without FastAPI or Streamlit:
  1.  DB init + create test user
  2.  Preference extraction  →  DB upsert
  3.  Planner               →  DB reads + web search + fetch plan
  4.  Article fetch         →  RSS feeds
  5.  Classifier            →  category labels
  6.  Deduplication         →  DB + URL + semantic passes
  7.  Ranking               →  relevance scores
  8.  Summarization         →  bullet summaries
  9.  Verification          →  accuracy check
  10. Digest composition    →  HTML digest saved to disk
  11. DB write              →  SentArticle rows persisted

Email delivery is intentionally skipped (no SMTP in test env).
The final HTML digest is saved to  pipeline_output_digest.html.
"""

import asyncio  # let you run multiple tasks concurrently (API CALLS or DB Queries)
import logging  # Logger
import os
import uuid   
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import select

load_dotenv()   # loads the variables from python env

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline_test")




# ── DB bootstrap (must happen before any model import) ───────────────────────
from db import session as db_session
from db.models import Article, Preference, SentArticle, User
from core.config import settings

db_session.init_db(settings.database_url)
logger.info("Database initialised.")


# ── Agent & service imports ───────────────────────────────────────────────────
from agents import (
    classifier_agent,
    preference_extraction_agent,
    ranking_agent,
    summarization_agent,
    verification_agent,
)
from agents import planner_agent
from services import article_fetcher, deduplication, digest_composition
from core.constants import RSS_FEED_URLS

SEPARATOR = "─" * 60


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def get_or_create_test_user(email: str) -> User:
    """Return existing test user or insert a new one."""
    async with db_session.AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()   # Method of Result Object, returned after executing a query
        if user is None:
            user = User(email=email, is_subscribed=True)
            session.add(user) # Creates session for a particular user 
            await session.commit()
            await session.refresh(user)
            logger.info("Created test user  id=%s  email=%s", user.id, user.email)
        else:
            logger.info("Found existing user  id=%s  email=%s", user.id, user.email)
        return user


async def save_sent_articles(user_id: uuid.UUID, articles: list[dict]) -> None:
    """Persist delivered articles to sent_articles table (avoids re-delivery)."""
    if not articles:
        return

    async with db_session.AsyncSessionLocal() as session:
        saved = 0
        for article in articles:
            url = article.get("url", "")
            if not url:
                continue

            # upsert Article row
            result = await session.execute(select(Article).where(Article.url == url))
            art_row = result.scalar_one_or_none()
            if art_row is None:
                art_row = Article(
                    url=url,
                    title=article.get("title", ""),
                    snippet=article.get("snippet", ""),
                    source=article.get("source_url", ""),
                    category=article.get("category"),
                )
                session.add(art_row)
                await session.flush()   # get art_row.id without full commit

            # insert SentArticle (skip if already exists)
            existing = await session.execute(
                select(SentArticle).where(
                    SentArticle.user_id == user_id,
                    SentArticle.article_id == art_row.id,
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(SentArticle(user_id=user_id, article_id=art_row.id))
                saved += 1

        await session.commit()
    logger.info("Saved %d sent_article rows to DB.", saved)


def _section(title: str) -> None:
    logger.info("")
    logger.info(SEPARATOR)
    logger.info("  %s", title)
    logger.info(SEPARATOR)


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────────────

async def run_pipeline() -> None:

    # ── Step 1: DB — get/create test user ────────────────────────────────────
    _section("STEP 1 · DB — get / create test user")
    TEST_EMAIL = "pipeline_test@insightstream.dev"
    user = await get_or_create_test_user(TEST_EMAIL)
    user_id = str(user.id)
    logger.info("user_id = %s", user_id)

    # ── Step 2: Preference extraction ────────────────────────────────────────
    _section("STEP 2 · Preference Extraction Agent  (Claude → DB upsert)")
    user_input = {
        "user_id": user_id,
        "text": (
            "I'm deeply interested in artificial intelligence, large language models, "
            "and FinTech innovations. Please exclude sports and entertainment news. "
            "Give me around 8 articles per digest."
        ),
    }
    structured_preferences = await preference_extraction_agent.run(user_input)
    logger.info("Extracted preferences: %s", structured_preferences)

    # ── Step 3: Planner ───────────────────────────────────────────────────────
    _section("STEP 3 · Planner Agent  (DB reads + web search + fetch plan)")
    planner_state = {
        "user_id": user_id,
        "structured_preferences": structured_preferences,
    }
    planner_result = await planner_agent.run(planner_state)
    fetch_plan = planner_result.get("fetch_plan", {})
    web_articles = planner_result.get("raw_articles", [])
    logger.info(
        "Fetch plan — sources: %d  category_weights: %s",
        len(fetch_plan.get("sources", [])),
        fetch_plan.get("category_weights", {}),
    )
    logger.info("Web search returned %d articles.", len(web_articles))

    # ── Step 4: Article fetch (RSS) ───────────────────────────────────────────
    _section("STEP 4 · Article Fetcher  (RSS feeds)")
    rss_articles = article_fetcher.fetch(RSS_FEED_URLS)
    logger.info("RSS fetched %d raw articles.", len(rss_articles))

    # Merge web-search articles + RSS articles
    all_raw_articles = web_articles + rss_articles
    logger.info("Total raw articles (web + RSS): %d", len(all_raw_articles))

    # ── Step 5: Classifier ────────────────────────────────────────────────────
    _section("STEP 5 · Classifier Agent  (Llama 3.3 70B)")
    classifier_state = {"raw_articles": all_raw_articles}
    classifier_result = classifier_agent.run(classifier_state)
    classified_articles = classifier_result.get("classified_articles", [])
    cats = {}
    for a in classified_articles:
        cats[a.get("category", "?")] = cats.get(a.get("category", "?"), 0) + 1
    logger.info("Classified %d articles: %s", len(classified_articles), cats)

    # ── Step 6: Deduplication ─────────────────────────────────────────────────
    _section("STEP 6 · Deduplication  (DB + URL + semantic)")
    deduplicated_articles = await deduplication.deduplicate(classified_articles, user_id)
    logger.info(
        "After deduplication: %d → %d articles.",
        len(classified_articles), len(deduplicated_articles),
    )

    # ── Step 7: Ranking ───────────────────────────────────────────────────────
    _section("STEP 7 · Ranking Agent  (Llama 3.3 70B)")
    ranking_state = {
        "deduplicated_articles": deduplicated_articles,
        "structured_preferences": structured_preferences,
    }
    ranking_result = ranking_agent.run(ranking_state)
    ranked_articles = ranking_result.get("ranked_articles", [])
    logger.info("Top %d articles selected.", len(ranked_articles))
    for i, a in enumerate(ranked_articles[:3], 1):
        logger.info("  #%d [score=%s] %s", i, a.get("score"), a.get("title", "")[:70])

    # ── Step 8: Summarization ─────────────────────────────────────────────────
    _section("STEP 8 · Summarization Agent  (Claude Sonnet 4.5)")
    summarization_state = {"ranked_articles": ranked_articles}
    summarization_result = summarization_agent.run(summarization_state)
    summaries = summarization_result.get("summaries", [])
    logger.info("Generated %d summaries.", len(summaries))

    # ── Step 9: Verification ──────────────────────────────────────────────────
    _section("STEP 9 · Verification Agent  (OpenAI)")
    verification_state = {
        "summaries": summaries,
        "ranked_articles": ranked_articles,
    }
    verification_result = verification_agent.run(verification_state)
    verified_summaries = verification_result.get("verified_summaries", [])
    logger.info(
        "Verification: %d/%d summaries passed.", len(verified_summaries), len(summaries)
    )

    # ── Step 10: Digest composition ───────────────────────────────────────────
    _section("STEP 10 · Digest Composition  (HTML)")
    digest_html = digest_composition.compose(verified_summaries, structured_preferences)
    output_path = "pipeline_output_digest.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(digest_html)
    logger.info("HTML digest saved → %s  (%d bytes)", output_path, len(digest_html))

    # ── Step 11: DB write — persist sent articles ─────────────────────────────
    _section("STEP 11 · DB Write  (save sent_article rows)")

    # Build a URL → category lookup from ranked_articles (classifier added category there)
    category_lookup = {a.get("url", ""): a.get("category") for a in ranked_articles}

    articles_to_save = [
        {
            **s,
            "source_url": s.get("source_url", s.get("url", "")),
            "category": s.get("category") or category_lookup.get(s.get("url", "")),
        }
        for s in verified_summaries
    ]
    await save_sent_articles(user.id, articles_to_save)

    # ── Summary ───────────────────────────────────────────────────────────────
    _section("PIPELINE COMPLETE")
    logger.info("user_id            : %s", user_id)
    logger.info("raw articles        : %d", len(all_raw_articles))
    logger.info("after dedup         : %d", len(deduplicated_articles))
    logger.info("ranked (top-N)      : %d", len(ranked_articles))
    logger.info("verified summaries  : %d", len(verified_summaries))
    logger.info("digest              : %s", output_path)
    logger.info(SEPARATOR)
    logger.info("Open pipeline_output_digest.html in a browser to see the result.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
