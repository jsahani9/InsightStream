"""Summarization Agent.

Generates concise bullet-point summaries with "why it matters" context
for each ranked article.
Model: Claude Sonnet 4.5 via AWS Bedrock.
"""

import json
import logging
import re

from core.bedrock_client import invoke_claude

logger = logging.getLogger(__name__)

SYSTEM = """You are a news digest summarization assistant.
Summarize the article into EXACTLY 3 bullet points followed by a "Why it matters" sentence.
STRICT RULES:
- EXACTLY 3 bullets. Not 2, not 4.
- Each bullet is EXACTLY 1 sentence. Max 20 words. No compound sentences joined with "and".
- Be specific — include names, numbers, and key facts. Cut all filler words.
- Never start a bullet with "The article", "This article", "The source", or "The piece".
- Only use facts explicitly stated in the article. Do NOT speculate or pad thin content.
- If the article lacks enough content for 3 distinct factual bullets, return an empty bullets list [].
- "why_it_matters": one punchy sentence, max 25 words, explains the real-world impact using facts from the article only. No vague filler like "this highlights" or "this shows"."""

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
        # Strip trailing commas before closing brackets/braces (LLM formatting issue)
        cleaned = re.sub(r',\s*([}\]])', r'\1', response[start:end])
        return json.loads(cleaned)
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

        bullets = parsed.get("bullets", [])
        why_it_matters = parsed.get("why_it_matters", "")

        # Hard drop — must have exactly 3 bullets and a non-empty why_it_matters
        if len(bullets) != 3 or not why_it_matters.strip():
            logger.warning(
                "Dropping article — got %d bullets (need 3): %s",
                len(bullets), article.get("title", "")[:60]
            )
            continue

        summaries.append({
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "source_url": article.get("source_url", ""),
            "published_at": article.get("published_at", ""),
            "category": article.get("category", ""),
            "score": article.get("score"),
            "bullets": bullets,
            "why_it_matters": why_it_matters,
        })
        logger.info("Summarized: %s", article.get("title", "")[:60])

    logger.info("Summarization: %d articles processed", len(summaries))
    return {"summaries": summaries}
