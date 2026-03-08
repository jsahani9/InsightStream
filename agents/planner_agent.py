"""Planner Agent.

Uses web search and DB query tools to decide which sources to fetch
and how to weight topic categories for the day's digest.
Model: GPT-5.1 via OpenAI.
"""


def run(state: dict) -> dict:
    """Plan fetch strategy based on user preferences and trending topics."""
    raise NotImplementedError
