"""Planner Agent.

Uses web search to discover trending topics and generates a fetch plan
with source priorities and category weights for the day's digest.
Model: OpenAI planner model.
"""

import json
import logging

from openai import OpenAI

from core.config import settings
from tools.web_search_tool import web_search

logger = logging.getLogger(__name__)

_openai_client = None

SYSTEM = """You are a news planning assistant.
Given user preferences and today's trending topics, decide which sources to fetch
and how to weight topic categories."""

USER_TEMPLATE = """
User preferences: {preferences}
Trending topics from web search: {trending}

Return a JSON fetch plan with keys: sources (list[url]), category_weights (dict).
"""


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _parse_fetch_plan(response: str) -> dict:
    """Extract JSON fetch plan from OpenAI response. Returns empty fallback on failure."""
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object in response")
        return json.loads(response[start:end])
    except Exception as e:
        logger.warning("Failed to parse fetch plan: %s", e)
        return {"sources": [], "category_weights": {}}


def run(state: dict) -> dict:
    """Plan fetch strategy based on user preferences and trending topics."""
    preferences = state.get("structured_preferences", {})
    topics = preferences.get("topics", [])

    # Search for trending topics per category
    web_articles = []
    trending_lines = []
    for topic in topics:
        results = web_search(query=f"latest {topic} news today", max_results=5)
        for r in results:
            web_articles.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", ""),
                "published_at": r.get("published_at", ""),
                "source_url": r.get("url", ""),
            })
        titles = [r["title"] for r in results[:3]]
        trending_lines.append(f"{topic}: {', '.join(titles)}")

    trending_text = "\n".join(trending_lines)

    prompt = USER_TEMPLATE.format(
        preferences=json.dumps(preferences),
        trending=trending_text,
    )

    client = _get_openai_client()
    response = client.chat.completions.create(
        model=settings.openai_planner_model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_completion_tokens=512,
    )

    raw_response = response.choices[0].message.content
    fetch_plan = _parse_fetch_plan(raw_response)

    logger.info("Planner: %d web articles fetched across %d topics", len(web_articles), len(topics))
    return {
        "fetch_plan": fetch_plan,
        "raw_articles": web_articles,
    }
