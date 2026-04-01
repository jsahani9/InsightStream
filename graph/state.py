"""LangGraph shared state schema.

Defines the TypedDict that flows through every node in the pipeline.
"""

from typing import TypedDict


class PipelineState(TypedDict):
    # ── Identity ──────────────────────────────────────────────────────────────
    user_id: str
    user_email: str

    # ── Preferences ───────────────────────────────────────────────────────────
    raw_preferences: dict
    structured_preferences: dict

    # ── Planning & fetching ───────────────────────────────────────────────────
    fetch_plan: dict
    raw_articles: list[dict]

    # ── Processing stages ─────────────────────────────────────────────────────
    classified_articles: list[dict]
    deduplicated_articles: list[dict]
    ranked_articles: list[dict]
    summaries: list[dict]
    verified_summaries: list[dict]
    digest: str

    # ── Retry counters (prevent infinite loops) ───────────────────────────────
    fetch_retry_count: int        # incremented each time we loop back to fetch
    summarization_retry_count: int  # incremented each time we loop back to summarize

    # ── Pipeline status (set when exiting early) ──────────────────────────────
    pipeline_status: str          # "success" | "no_new_articles" | "no_summaries"

    # ── Trigger mode ──────────────────────────────────────────────────────────
    on_demand: bool               # True = user clicked "Get News Now", skip subscription check
