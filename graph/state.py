"""LangGraph shared state schema.

Defines the TypedDict that flows through every node in the pipeline.
"""

from typing import TypedDict


class PipelineState(TypedDict):
    user_id: str
    user_email: str
    raw_preferences: dict
    structured_preferences: dict
    fetch_plan: dict
    raw_articles: list[dict]
    classified_articles: list[dict]
    deduplicated_articles: list[dict]
    ranked_articles: list[dict]
    summaries: list[dict]
    verified_summaries: list[dict]
    digest: str
