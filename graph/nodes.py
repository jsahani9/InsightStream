"""LangGraph node wrappers.

Each function wraps one agent or service call and conforms to the
LangGraph node contract:
  - Input  : full PipelineState dict
  - Output : dict of ONLY the keys this node updates

Async nodes  (call async agents/services):
  preference_extraction_node, planner_node,
  deduplication_node, email_delivery_node

Sync nodes (call sync agents/services):
  fetch_articles_node, classifier_node, ranking_node,
  summarization_node, verification_node, digest_composition_node
"""

import logging
import uuid

from sqlalchemy import select

from agents import (
    classifier_agent,
    preference_extraction_agent,
    ranking_agent,
    summarization_agent,
    verification_agent,
)
from agents import planner_agent
from core.constants import RSS_FEED_URLS
from db import session as db_session
from db.models import Article, SentArticle
from services import article_fetcher, deduplication, digest_composition
from services.email_delivery import send as email_send

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Node 1 — Preference Extraction  (async)
# Reads : user_id, raw_preferences
# Writes: structured_preferences
# ─────────────────────────────────────────────────────────────────────────────
async def preference_extraction_node(state: dict) -> dict:
    """Extract structured preferences from raw user text and upsert to DB."""
    user_input = {
        "user_id": state["user_id"],
        "text": state.get("raw_preferences", {}).get("text", ""),
    }
    structured = await preference_extraction_agent.run(user_input)
    logger.info("Node [preference_extraction]: %s", structured)
    return {"structured_preferences": structured}


# ─────────────────────────────────────────────────────────────────────────────
# Node 2 — Planner  (async)
# Reads : user_id, structured_preferences
# Writes: fetch_plan, raw_articles, structured_preferences (refreshed from DB)
# ─────────────────────────────────────────────────────────────────────────────
async def planner_node(state: dict) -> dict:
    """Read DB preferences + sent history, run web search, build fetch plan."""
    result = await planner_agent.run(state)
    logger.info(
        "Node [planner]: %d web articles, %d sources in plan",
        len(result.get("raw_articles", [])),
        len(result.get("fetch_plan", {}).get("sources", [])),
    )
    return {
        "fetch_plan": result.get("fetch_plan", {}),
        "raw_articles": result.get("raw_articles", []),
        "structured_preferences": result.get(
            "structured_preferences", state.get("structured_preferences", {})
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 3 — Fetch Articles  (sync)
# Reads : fetch_plan, raw_articles (web articles already fetched by planner)
# Writes: raw_articles (merges RSS with planner's web articles)
# ─────────────────────────────────────────────────────────────────────────────
def fetch_articles_node(state: dict) -> dict:
    """Fetch RSS articles and merge with web articles already in state."""
    sources = state.get("fetch_plan", {}).get("sources") or RSS_FEED_URLS
    rss_articles = article_fetcher.fetch(sources)
    web_articles = state.get("raw_articles", [])
    merged = web_articles + rss_articles
    logger.info(
        "Node [fetch_articles]: %d web + %d RSS = %d total",
        len(web_articles), len(rss_articles), len(merged),
    )
    return {"raw_articles": merged}


# ─────────────────────────────────────────────────────────────────────────────
# Node 4 — Classifier  (sync)
# Reads : raw_articles
# Writes: classified_articles
# ─────────────────────────────────────────────────────────────────────────────
def classifier_node(state: dict) -> dict:
    """Label each article as AI, FinTech, or Tech using Llama."""
    result = classifier_agent.run(state)
    classified = result.get("classified_articles", [])
    logger.info("Node [classifier]: %d articles classified.", len(classified))
    return {"classified_articles": classified}


# ─────────────────────────────────────────────────────────────────────────────
# Node 5 — Deduplication  (async)
# Reads : classified_articles, user_id
# Writes: deduplicated_articles
# ─────────────────────────────────────────────────────────────────────────────
async def deduplication_node(state: dict) -> dict:
    """Remove already-sent, URL-duplicate, and semantically similar articles."""
    articles = state.get("classified_articles", [])
    user_id = state.get("user_id", "")
    deduped = await deduplication.deduplicate(articles, user_id)
    logger.info(
        "Node [deduplication]: %d → %d articles.", len(articles), len(deduped)
    )
    return {"deduplicated_articles": deduped}


# ─────────────────────────────────────────────────────────────────────────────
# Node 6 — Ranking  (sync)
# Reads : deduplicated_articles, structured_preferences
# Writes: ranked_articles
# ─────────────────────────────────────────────────────────────────────────────
def ranking_node(state: dict) -> dict:
    """Score articles by relevance and select the top-N using Llama."""
    result = ranking_agent.run(state)
    ranked = result.get("ranked_articles", [])
    logger.info("Node [ranking]: top %d articles selected.", len(ranked))
    return {"ranked_articles": ranked}


# ─────────────────────────────────────────────────────────────────────────────
# Node 7 — Summarization  (sync)
# Reads : ranked_articles
# Writes: summaries
# ─────────────────────────────────────────────────────────────────────────────
def summarization_node(state: dict) -> dict:
    """Generate bullet-point summaries with 'why it matters' using Claude."""
    result = summarization_agent.run(state)
    summaries = result.get("summaries", [])
    logger.info("Node [summarization]: %d summaries generated.", len(summaries))
    return {"summaries": summaries}


# ─────────────────────────────────────────────────────────────────────────────
# Node 8 — Verification  (sync)
# Reads : summaries, ranked_articles
# Writes: verified_summaries
# ─────────────────────────────────────────────────────────────────────────────
def verification_node(state: dict) -> dict:
    """Verify summaries for factual accuracy; retry failed ones via Claude."""
    result = verification_agent.run(state)
    verified = result.get("verified_summaries", [])
    logger.info(
        "Node [verification]: %d/%d summaries passed.",
        len(verified), len(state.get("summaries", [])),
    )
    return {"verified_summaries": verified}


# ─────────────────────────────────────────────────────────────────────────────
# Node 9 — Digest Composition  (sync)
# Reads : verified_summaries, structured_preferences
# Writes: digest
# ─────────────────────────────────────────────────────────────────────────────
def digest_composition_node(state: dict) -> dict:
    """Assemble verified summaries into an HTML digest."""
    html = digest_composition.compose(
        verified_summaries=state.get("verified_summaries", []),
        user_preferences=state.get("structured_preferences", {}),
    )
    logger.info("Node [digest_composition]: %d bytes.", len(html))
    return {"digest": html}


# ─────────────────────────────────────────────────────────────────────────────
# Node 10 — Email Delivery  (async)
# Reads : user_id, user_email, digest, verified_summaries, ranked_articles
# Writes: {} (side effects only: email sent + DB rows saved)
# ─────────────────────────────────────────────────────────────────────────────
async def email_delivery_node(state: dict) -> dict:
    """Send the digest email and persist delivered articles to the DB.

    Uses user_email directly from state (set when the pipeline is initialised).
    Subscription gate is enforced inside email_send().
    After sending, Article + SentArticle rows are written so deduplication
    works correctly on the next run.
    """
    user_id_str: str = state.get("user_id", "")
    user_email: str = state.get("user_email", "")
    digest: str = state.get("digest", "")

    if not user_id_str or not user_email:
        logger.warning("Node [email_delivery]: missing user_id or user_email — skipping.")
        return {}

    # Send email (subscription check is inside email_send)
    await email_send(user_id=user_id_str, user_email=user_email, digest=digest)

    # Persist delivered articles to DB
    verified_summaries = state.get("verified_summaries", [])
    ranked_articles = state.get("ranked_articles", [])
    category_lookup = {a.get("url", ""): a.get("category") for a in ranked_articles}
    uid = uuid.UUID(user_id_str)

    if db_session.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with db_session.AsyncSessionLocal() as session:
        saved = 0
        for summary in verified_summaries:
            url = summary.get("url", "")
            if not url:
                continue

            # Upsert Article row
            res = await session.execute(select(Article).where(Article.url == url))
            art = res.scalar_one_or_none()
            if art is None:
                art = Article(
                    url=url,
                    title=summary.get("title", ""),
                    snippet=summary.get("snippet", ""),
                    source=summary.get("source_url", ""),
                    category=summary.get("category") or category_lookup.get(url),
                )
                session.add(art)
                await session.flush()

            # Insert SentArticle only if not already present
            existing = await session.execute(
                select(SentArticle).where(
                    SentArticle.user_id == uid,
                    SentArticle.article_id == art.id,
                )
            )
            if existing.scalar_one_or_none() is None:
                session.add(SentArticle(user_id=uid, article_id=art.id))
                saved += 1

        await session.commit()

    logger.info(
        "Node [email_delivery]: email sent to %s, %d articles saved to DB.",
        user_email, saved,
    )
    return {}
