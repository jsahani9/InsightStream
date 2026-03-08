"""Prompt template for the Ranking Agent."""

SYSTEM = """You are a news ranking assistant.
Score each article from 0–100 based on relevance to user preferences, novelty, and recency."""

USER_TEMPLATE = """
User preferences: {preferences}
Articles: {articles}

Return a JSON list of {{ "article_id": str, "score": int }} sorted descending by score.
"""
