"""Semantic deduplication service.

Three-pass deduplication:
  0. DB check — drop articles already sent to this user in the last 7 days.
  1. Exact URL match — drop duplicates within the current batch.
  2. OpenAI embeddings + cosine similarity — catches the same story
     published across multiple sources.


    - Before : only removes duplicates within the current batch of freshly fetched articles, 
    But ignores articles that were already send to the under in the past 7 days
    
"""

import logging

import numpy as np
from openai import OpenAI

from core.config import settings
from tools.database_query_tool import get_recently_sent_articles

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.75


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



# Uses 3 passes to check the duplicates 

async def deduplicate(articles: list[dict], user_id: str) -> list[dict]:
    """Remove duplicate and near-duplicate articles.

    Pass 0 filters articles the user already received (DB lookup).
    Pass 1 removes URL-level duplicates within the current batch.
    Pass 2 removes semantically similar articles via embeddings.
    """
    if not articles:
        return []

    # Pass 0: drop articles already sent to this user in the last 7 days
    recently_sent_ids: set[str] = set(
        await get_recently_sent_articles(user_id, days=7)
    )
    if recently_sent_ids:
        before = len(articles)
        articles = [
            a for a in articles
            if str(a.get("id", "")) not in recently_sent_ids
        ]
        logger.info(
            "After DB dedup (already sent): %d → %d articles", before, len(articles)
        )

    if not articles:
        return []

    # Pass 1: exact URL deduplication within the current batch
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
