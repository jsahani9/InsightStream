"""Planner Agent.

Uses web search and DB query tools to decide which sources to fetch
and how to weight topic categories for the day's digest.
Model: GPT-5.1 via OpenAI.
"""

SYSTEM = """You are a news planning assistant.
Given user preferences and today's trending topics, decide which sources to fetch
and how to weight topic categories."""

USER_TEMPLATE = """
User preferences: {preferences}
Trending topics from web search: {trending}

Return a JSON fetch plan with keys: sources (list[url]), category_weights (dict).
"""


def run(state: dict) -> dict:
    """Plan fetch strategy based on user preferences and trending topics."""
    raise NotImplementedError
