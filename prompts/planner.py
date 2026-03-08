"""Prompt template for the Planner Agent."""

SYSTEM = """You are a news planning assistant.
Given user preferences and today's trending topics, decide which sources to fetch
and how to weight topic categories."""

USER_TEMPLATE = """
User preferences: {preferences}
Trending topics from web search: {trending}

Return a JSON fetch plan with keys: sources (list[url]), category_weights (dict).
"""
