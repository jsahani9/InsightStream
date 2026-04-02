"""Ranking Agent.

Scores deduplicated articles by relevance to user preferences,
novelty, and recency.
Model: Llama 3.3 70B via AWS Bedrock.
"""

import json
import logging

from core.bedrock_client import invoke_llama

logger = logging.getLogger(__name__)

TOP_N = 5

SYSTEM = """You are a news ranking assistant.
Score each article from 0 to 100 based on relevance to user preferences, novelty, and recency.
Return only valid JSON."""

USER_TEMPLATE = """User preferences: {preferences}

Articles to rank:
{articles}

Return ONLY a valid JSON array like:
[{{"id": 0, "score": 85}}, {{"id": 1, "score": 42}}]

Include all article IDs exactly once.
Sort descending by score.
"""


def _parse_scores(response: str, num_articles: int) -> list[dict[str, int]]:
    """Extract JSON array from LLM response. Falls back to default scores."""
    try:
        start = response.find("[")
        end = response.rfind("]") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON array found in response")

        raw_scores = json.loads(response[start:end])

        cleaned_scores: list[dict[str, int]] = []
        seen_ids: set[int] = set()

        for item in raw_scores:
            article_id = item.get("id")
            score = item.get("score")

            if not isinstance(article_id, int):
                continue
            if article_id in seen_ids:
                continue
            if not (0 <= article_id < num_articles):
                continue

            try:
                score = int(score)
            except (TypeError, ValueError):
                score = 50

            score = max(0, min(100, score))

            cleaned_scores.append({"id": article_id, "score": score})
            seen_ids.add(article_id)

        for i in range(num_articles):
            if i not in seen_ids:
                cleaned_scores.append({"id": i, "score": 50})

        return cleaned_scores

    except Exception as e:
        logger.error("Failed to parse ranking response: %s", e)
        return [{"id": i, "score": 50} for i in range(num_articles)]


def run(state: dict) -> dict:
    """Rank articles and return top N for summarization."""
    articles = state.get("deduplicated_articles", [])
    preferences = state.get("structured_preferences", {})

    if not articles:
        return {"ranked_articles": []}

    article_list = "\n".join(
        f'[{i}] {a.get("title", "")} | {a.get("source_url", "")} | {a.get("published_at", "")}'
        for i, a in enumerate(articles)
    )

    prompt = USER_TEMPLATE.format(
        preferences=json.dumps(preferences),
        articles=article_list,
    )

    response = invoke_llama(
        prompt=prompt,
        system=SYSTEM,
        max_gen_len=2048,
        temperature=0.1,
    )

    scores = _parse_scores(response, len(articles))
    scored = sorted(scores, key=lambda x: x["score"], reverse=True)

    top_n = preferences.get("article_count", TOP_N)
    buffer_n = top_n * 3  # large buffer so drops in enrichment/summarization don't starve final count

    # Category diversity for the buffer: each category can contribute up to top_n articles.
    # Diversity for the final delivered set is enforced by the verification trim.
    max_per_category = top_n
    category_counts: dict[str, int] = {}
    ranked_articles = []

    for item in scored:
        if len(ranked_articles) >= buffer_n:
            break
        idx = item["id"]
        article = dict(articles[idx])
        cat = article.get("category") or "Other"
        if category_counts.get(cat, 0) >= max_per_category:
            continue
        article["score"] = item["score"]
        ranked_articles.append(article)
        category_counts[cat] = category_counts.get(cat, 0) + 1

    logger.info("Ranking: %d -> top %d articles (buffer for %d requested, diversity: %s)",
                len(articles), len(ranked_articles), top_n, category_counts)
    return {"ranked_articles": ranked_articles}