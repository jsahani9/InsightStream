"""LangGraph pipeline definition.

Wires all 10 agent/service nodes into a StateGraph with conditional
routing so the pipeline can retry or exit early when results don't
meet quality thresholds.

Pipeline flow:
  START
    → preference_extraction
    → planner
    → fetch_articles  ←──────────────────────────────┐
    → classifier                                      │  (retry once if too few articles)
    → deduplication                                   │
        │ no new articles → END (no_new_articles)      │
        ↓                                             │
    → ranking ────────────────────────────────────────┘
        │ still too few → END (no_new_articles)
        ↓
    → summarization  ←───────────────────────────────┐
    → verification                                    │  (retry once if all summaries fail)
        │ no summaries passed → END (no_summaries)    │
        │ still failing after retry → END             │
        ↓                                             │
    → digest_composition ─────────────────────────────┘
    → email_delivery
    → END (success)

Conditional routing decisions:
  1. route_after_dedup         — exits early if 0 articles survive deduplication
  2. route_after_ranking        — loops back to fetch_articles once if < MIN_ARTICLES
  3. route_after_verification   — loops back to summarization once if 0 summaries passed

Usage:
    from core.config import settings
    from db.session import init_db
    from graph.pipeline import build_pipeline

    init_db(settings.database_url)
    pipeline = build_pipeline()

    result = await pipeline.ainvoke({
        "user_id":                  "<uuid>",
        "user_email":               "<email>",
        "raw_preferences":          {"text": "I like AI and FinTech…"},
        "fetch_retry_count":        0,
        "summarization_retry_count": 0,
        "pipeline_status":          "",
    })
"""

import asyncio
import logging

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    classifier_node,
    deduplication_node,
    digest_composition_node,
    email_delivery_node,
    enrich_and_filter_node,
    fetch_articles_node,
    planner_node,
    preference_extraction_node,
    ranking_node,
    summarization_node,
    verification_node,
)
from graph.state import PipelineState

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────
MIN_ARTICLES_FOR_DIGEST = 3   # minimum ranked articles needed to produce a digest
MAX_FETCH_RETRIES = 1         # how many extra fetch passes are allowed
MAX_SUMMARIZATION_RETRIES = 1 # how many extra summarization passes are allowed


# ─────────────────────────────────────────────────────────────────────────────
# Conditional routing functions
# Each returns the name of the next node (or END).
# ─────────────────────────────────────────────────────────────────────────────

def route_after_dedup(state: dict) -> str:
    """Exit early if deduplication left no new articles for this user."""
    articles = state.get("deduplicated_articles", [])
    if not articles:
        logger.warning("route_after_dedup: 0 articles after dedup — exiting early.")
        return "end_no_articles"
    logger.info("route_after_dedup: %d articles → proceeding to ranking.", len(articles))
    return "ranking"


def route_after_ranking(state: dict) -> str:
    """If too few articles were ranked, retry fetching once (expanded sources).
    After one retry, proceed regardless to avoid an infinite loop.
    """
    ranked = state.get("ranked_articles", [])
    retry_count = state.get("fetch_retry_count", 0)

    if len(ranked) < MIN_ARTICLES_FOR_DIGEST and retry_count < MAX_FETCH_RETRIES:
        logger.warning(
            "route_after_ranking: only %d articles ranked (min %d) — retrying fetch (attempt %d).",
            len(ranked), MIN_ARTICLES_FOR_DIGEST, retry_count + 1,
        )
        return "fetch_articles"

    if not ranked:
        logger.warning("route_after_ranking: 0 articles after ranking — exiting early.")
        return "end_no_articles"

    logger.info("route_after_ranking: %d articles → proceeding to summarization.", len(ranked))
    return "summarization"


def route_after_verification(state: dict) -> str:
    """If all summaries failed verification, retry summarization once.
    After one retry, exit early to avoid sending a low-quality digest.
    """
    verified = state.get("verified_summaries", [])
    retry_count = state.get("summarization_retry_count", 0)

    if not verified and retry_count < MAX_SUMMARIZATION_RETRIES:
        logger.warning(
            "route_after_verification: 0 summaries passed — retrying summarization (attempt %d).",
            retry_count + 1,
        )
        return "summarization"

    if not verified:
        logger.warning("route_after_verification: 0 summaries after retry — exiting early.")
        return "end_no_summaries"

    logger.info(
        "route_after_verification: %d summaries verified → proceeding to digest.", len(verified)
    )
    return "digest_composition"


# ── Early-exit stub nodes ─────────────────────────────────────────────────────

def end_no_articles_node(state: dict) -> dict:
    """Terminal node: pipeline stopped because no new articles were found."""
    logger.info("Pipeline ended early: no new articles for user %s.", state.get("user_id"))
    return {"pipeline_status": "no_new_articles"}


def end_no_summaries_node(state: dict) -> dict:
    """Terminal node: pipeline stopped because no summaries passed verification."""
    logger.info("Pipeline ended early: no verified summaries for user %s.", state.get("user_id"))
    return {"pipeline_status": "no_summaries"}


# ── Retry counter bump nodes ──────────────────────────────────────────────────

def bump_fetch_retry(state: dict) -> dict:
    """Increment fetch_retry_count before looping back to fetch_articles."""
    return {"fetch_retry_count": state.get("fetch_retry_count", 0) + 1}


def bump_summarization_retry(state: dict) -> dict:
    """Increment summarization_retry_count before looping back to summarization."""
    return {"summarization_retry_count": state.get("summarization_retry_count", 0) + 1}


# ─────────────────────────────────────────────────────────────────────────────
# Graph builder
# ─────────────────────────────────────────────────────────────────────────────

def build_pipeline():
    """Build and return the compiled LangGraph pipeline with conditional routing."""
    graph = StateGraph(PipelineState)

    # ── Core pipeline nodes ───────────────────────────────────────────────────
    graph.add_node("preference_extraction",  preference_extraction_node)
    graph.add_node("planner",                planner_node)
    graph.add_node("fetch_articles",         fetch_articles_node)
    graph.add_node("classifier",             classifier_node)
    graph.add_node("deduplication",          deduplication_node)
    graph.add_node("ranking",                ranking_node)
    graph.add_node("enrich_and_filter",      enrich_and_filter_node)
    graph.add_node("summarization",          summarization_node)
    graph.add_node("verification",           verification_node)
    graph.add_node("digest_composition",     digest_composition_node)
    graph.add_node("email_delivery",         email_delivery_node)

    # ── Early-exit nodes ──────────────────────────────────────────────────────
    graph.add_node("end_no_articles",        end_no_articles_node)
    graph.add_node("end_no_summaries",       end_no_summaries_node)

    # ── Retry counter bump nodes ──────────────────────────────────────────────
    graph.add_node("bump_fetch_retry",       bump_fetch_retry)
    graph.add_node("bump_summarization_retry", bump_summarization_retry)

    # ── Linear edges (no decision needed) ────────────────────────────────────
    graph.add_edge(START,                    "preference_extraction")
    graph.add_edge("preference_extraction",  "planner")
    graph.add_edge("planner",                "fetch_articles")
    graph.add_edge("fetch_articles",         "classifier")
    graph.add_edge("classifier",             "deduplication")

    # ── Conditional: after deduplication ─────────────────────────────────────
    graph.add_conditional_edges(
        "deduplication",
        route_after_dedup,
        {
            "ranking":          "ranking",
            "end_no_articles":  "end_no_articles",
        },
    )

    # ── Conditional: after ranking ────────────────────────────────────────────
    graph.add_conditional_edges(
        "ranking",
        route_after_ranking,
        {
            "summarization":    "enrich_and_filter",  # enrich content + drop thin articles first
            "fetch_articles":   "bump_fetch_retry",
            "end_no_articles":  "end_no_articles",
        },
    )
    graph.add_edge("enrich_and_filter", "summarization")
    # retry loop: bump counter → back to fetch_articles
    graph.add_edge("bump_fetch_retry",       "fetch_articles")

    # ── Linear edges: summarization → verification ────────────────────────────
    graph.add_edge("summarization",          "verification")

    # ── Conditional: after verification ──────────────────────────────────────
    graph.add_conditional_edges(
        "verification",
        route_after_verification,
        {
            "digest_composition":   "digest_composition",
            "summarization":        "bump_summarization_retry",  # bump then re-summarize
            "end_no_summaries":     "end_no_summaries",
        },
    )
    # retry loop: bump counter → back to summarization
    graph.add_edge("bump_summarization_retry", "summarization")

    # ── Final linear edges ────────────────────────────────────────────────────
    graph.add_edge("digest_composition",     "email_delivery")
    graph.add_edge("email_delivery",         END)

    # ── Early-exit edges → END ────────────────────────────────────────────────
    graph.add_edge("end_no_articles",        END)
    graph.add_edge("end_no_summaries",       END)

    return graph.compile()


# ─────────────────────────────────────────────────────────────────────────────
# Entry point — run the full pipeline for a known user
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    load_dotenv()

    from core.config import settings
    from db.session import init_db

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )

    init_db(settings.database_url)
    pipeline = build_pipeline()

    initial_state = {
        "user_id":                   "416039ba-61a1-4960-ac38-1d9ef4acf080",
        "user_email":                "akash7@my.yorku.ca",
        "raw_preferences":           {
            "text": "I'm interested in AI and FinTech news. Exclude crypto. Send me 5 articles a day."
        },
        "structured_preferences":    {},
        "fetch_plan":                {},
        "raw_articles":              [],
        "classified_articles":       [],
        "deduplicated_articles":     [],
        "ranked_articles":           [],
        "summaries":                 [],
        "verified_summaries":        [],
        "digest":                    "",
        "fetch_retry_count":         0,
        "summarization_retry_count": 0,
        "pipeline_status":           "",
    }

    logger.info("Starting InsightStream pipeline via LangGraph…")
    result = await pipeline.ainvoke(initial_state)

    status = result.get("pipeline_status", "success")
    verified = result.get("verified_summaries", [])
    logger.info("Pipeline finished — status: %s | summaries: %d", status, len(verified))


if __name__ == "__main__":
    asyncio.run(main())
