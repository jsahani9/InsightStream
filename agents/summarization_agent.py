"""Summarization Agent.

Generates concise bullet-point summaries with "why it matters" context
for each ranked article.
Model: Claude Sonnet 4.5 via AWS Bedrock.
"""

import json
import logging

from core.bedrock_client import invoke_claude

logger = logging.getLogger(__name__)

SYSTEM = """You are a technical news summarization assistant.
Summarize the article into EXACTLY 3 bullet points followed by a "Why it matters" sentence.
Rules:
- EXACTLY 3 bullets. No more, no fewer.
- EXACTLY 2 sentences per bullet. No more, no fewer.
- Write in active voice. Be direct and specific — include company names, numbers, and key facts.
- Never start a bullet with "The article", "This article", "The source", or "The piece".
- If the content is thin, infer reasonable context from the title and what is available. Do not mention lack of information."""

USER_TEMPLATE = """
Article title: {title}
Article content: {text}

Return JSON: {{ "bullets": list[str], "why_it_matters": str }}
"""


def _parse_summary(response: str) -> dict:
    """Extract JSON summary from Claude response. Returns empty fallback on failure."""
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object in response")
        return json.loads(response[start:end])
    except Exception as e:
        logger.warning("Failed to parse summary response: %s", e)
        return {"bullets": [], "why_it_matters": ""}


def run(state: dict) -> dict:
    """Summarize ranked articles into digest-ready insights."""
    articles = state.get("ranked_articles", [])

    if not articles:
        return {"summaries": []}

    summaries = []
    for article in articles:
        prompt = USER_TEMPLATE.format(
            title=article.get("title", ""),
            text=article.get("content") or article.get("snippet", ""),
        )
        response = invoke_claude(prompt=prompt, system=SYSTEM, max_tokens=768, temperature=0.3)
        parsed = _parse_summary(response)

        summaries.append({
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "source_url": article.get("source_url", ""),
            "published_at": article.get("published_at", ""),
            "score": article.get("score"),
            "bullets": parsed.get("bullets", []),
            "why_it_matters": parsed.get("why_it_matters", ""),
        })
        logger.info("Summarized: %s", article.get("title", "")[:60])

    logger.info("Summarization: %d articles processed", len(summaries))
    return {"summaries": summaries}
