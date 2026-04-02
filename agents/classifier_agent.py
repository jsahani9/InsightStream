"""Classifier Agent.

Labels each fetched article into a dynamic user-defined category.
Model: Llama 3.3 70B via AWS Bedrock.

Flow:
  1. Read raw_articles from pipeline state.
  2. Read categories from structured_preferences (set by preference extraction).
  3. For each article, send title + snippet to Llama on Bedrock.
  4. Parse the returned category label.
  5. Attach the category to the article dict.
  6. Return classified_articles to the pipeline state.
"""

import json
import logging

from core.bedrock_client import invoke_llama

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = ["AI", "Tech", "FinTech", "Crypto", "Markets", "World"]

USER_TEMPLATE = """Article title: {title}
Article snippet: {snippet}

Return JSON: {{ "category": "<one of the categories listed above>" }}"""


def _parse_category(response: str, valid_categories: set, default_category: str) -> str:
    """Extract category label from Llama response.

    Falls back to default_category if parsing fails or label is unrecognised.
    """
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object in response")
        parsed = json.loads(response[start:end])
        category = str(parsed.get("category", "")).strip()
        if category in valid_categories:
            return category
        # Try case-insensitive match
        for valid in valid_categories:
            if category.lower() == valid.lower():
                return valid
        logger.warning("Unrecognised category %r — defaulting to %s", category, default_category)
    except Exception as e:
        logger.warning("Failed to parse classifier response: %s", e)

    return default_category


def run(state: dict) -> dict:
    """Classify articles by topic category using dynamic user categories.

    Reads categories from structured_preferences (set by preference extraction).
    Falls back to DEFAULT_CATEGORIES if not set.
    """
    articles = state.get("raw_articles", [])

    if not articles:
        logger.info("Classifier: no articles to classify.")
        return {"classified_articles": []}

    categories = state.get("structured_preferences", {}).get("categories") or DEFAULT_CATEGORIES
    valid_categories = set(categories)
    default_category = categories[0] if categories else "Tech"

    cat_list = "\n".join(f"- {cat}" for cat in categories)
    system = f"""You are a news classification assistant.
Classify each article into exactly one of these categories:
{cat_list}
Return ONLY a valid JSON object. No explanation."""

    classified = []
    for article in articles:
        prompt = USER_TEMPLATE.format(
            title=article.get("title", ""),
            snippet=article.get("snippet", ""),
        )
        response = invoke_llama(prompt=prompt, system=system, max_gen_len=64, temperature=0.1)
        category = _parse_category(response, valid_categories, default_category)

        classified.append({**article, "category": category})
        logger.info("Classified [%s]: %s", category, article.get("title", "")[:60])

    logger.info("Classifier: %d articles classified.", len(classified))
    return {"classified_articles": classified}
