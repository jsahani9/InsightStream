"""Classifier Agent.

Labels each fetched article into a category: AI, FinTech, or Tech.
Model: Llama 3.3 70B via AWS Bedrock.

Flow:
  1. Read raw_articles from pipeline state.
  2. For each article, send title + snippet to Llama on Bedrock.
  3. Parse the returned category label.
  4. Attach the category to the article dict.
  5. Return classified_articles to the pipeline state.
"""

import json
import logging

from core.bedrock_client import invoke_llama

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"AI", "FinTech", "Tech"}
DEFAULT_CATEGORY = "Tech"

SYSTEM = """You are a news classification assistant.
Classify each article into exactly one category: AI, FinTech, or Tech.
- AI       : artificial intelligence, machine learning, LLMs, robotics, automation
- FinTech  : financial technology, payments, banking, crypto, investing, markets
- Tech     : general technology, software, hardware, cybersecurity, startups
Return ONLY a valid JSON object. No explanation."""

USER_TEMPLATE = """Article title: {title}
Article snippet: {snippet}

Return JSON: {{ "category": "<AI|FinTech|Tech>" }}"""


def _parse_category(response: str) -> str:
    """Extract category label from Llama response.

    Falls back to DEFAULT_CATEGORY if parsing fails or label is unrecognised.
    """
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object in response")
        parsed = json.loads(response[start:end])
        category = str(parsed.get("category", "")).strip()
        if category in VALID_CATEGORIES:
            return category
        logger.warning("Unrecognised category %r — defaulting to %s", category, DEFAULT_CATEGORY)
    except Exception as e:
        logger.warning("Failed to parse classifier response: %s", e)

    return DEFAULT_CATEGORY


def run(state: dict) -> dict:
    """Classify articles by topic category.

    Reads raw_articles from state, classifies each one via Llama,
    and returns classified_articles with a 'category' field added.
    """
    articles = state.get("raw_articles", [])

    if not articles:
        logger.info("Classifier: no articles to classify.")
        return {"classified_articles": []}

    classified = []
    for article in articles:
        prompt = USER_TEMPLATE.format(
            title=article.get("title", ""),
            snippet=article.get("snippet", ""),
        )
        response = invoke_llama(prompt=prompt, system=SYSTEM, max_gen_len=64, temperature=0.1)
        category = _parse_category(response)

        classified.append({**article, "category": category})
        logger.info(
            "Classified [%s]: %s", category, article.get("title", "")[:60]
        )

    logger.info("Classifier: %d articles classified.", len(classified))
    return {"classified_articles": classified}
