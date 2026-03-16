"""Ranking Agent.

Scores deduplicated articles by relevance to user preferences,
novelty, and recency. Queries live preferences via the DB query tool.
Model: Llama 3.3 70B via AWS Bedrock.
"""

SYSTEM = """You are a news ranking assistant.
Score each article from 0–100 based on relevance to user preferences, novelty, and recency."""

USER_TEMPLATE = """
User preferences: {preferences}
Articles: {articles}

Return a JSON list of {{ "article_id": str, "score": int }} sorted descending by score.
"""


def run(state: dict) -> dict:
    """Rank articles and return top N for summarization."""
    raise NotImplementedError
