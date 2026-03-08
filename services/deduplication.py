"""Semantic deduplication service.

Uses OpenAI embeddings to compute cosine similarity between articles
and filters out near-duplicate stories. Also checks recently sent
articles via the database query tool.
"""


def deduplicate(articles: list[dict], user_id: str) -> list[dict]:
    """Remove duplicate and previously sent articles."""
    raise NotImplementedError
