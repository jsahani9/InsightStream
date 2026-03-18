"""Semantic deduplication service.

Two-pass deduplication:
  1. Exact URL match.
  2. OpenAI embeddings + cosine similarity — catches the same story
     published across multiple sources.

TODO: Add DB check for articles already sent to user (needs db/models.py).
"""

import logging

import numpy as np
from openai import OpenAI

from core.config import settings

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.92


def _get_embeddings(texts: list[str]) -> list[list[float]]:
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def deduplicate(articles: list[dict], user_id: str) -> list[dict]:
    """Remove duplicate and near-duplicate articles."""
    if not articles:
        return []

    # Pass 1: exact URL deduplication
    seen_urls: set[str] = set()
    unique = []
    for article in articles:
        url = article.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique.append(article)

    logger.info("After URL dedup: %d → %d articles", len(articles), len(unique))

    # Pass 2: semantic deduplication via embeddings
    texts = [f"{a['title']} {a['snippet']}" for a in unique]
    embeddings = _get_embeddings(texts)

    keep = []
    kept_embeddings = []

    for article, emb in zip(unique, embeddings):
        is_duplicate = any(
            _cosine_similarity(emb, kept_emb) >= SIMILARITY_THRESHOLD
            for kept_emb in kept_embeddings
        )
        if not is_duplicate:
            keep.append(article)
            kept_embeddings.append(emb)

    logger.info("After semantic dedup: %d → %d articles", len(unique), len(keep))
    return keep
