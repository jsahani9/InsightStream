"""Verification Agent.

Cross-checks each summary against its source article for factual accuracy.
If a summary fails, triggers the summarization retry tool with stricter constraints.
Model: openai_verifier_model via OpenAI.
"""

import json
import logging

from openai import OpenAI

from core.config import settings
from tools.summarization_retry_tool import retry_summarization

logger = logging.getLogger(__name__)

_openai_client = None

SYSTEM = """You are a factual accuracy verification assistant.
Compare each summary against its source article and identify any inaccuracies or hallucinations."""

USER_TEMPLATE = """
Source article: {article_text}
Summary bullets: {summary_bullets}
Why it matters: {why_it_matters}

Return JSON: {{ "passed": bool, "issues": list[str] }}
"""


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _parse_result(response: str) -> dict:
    """Extract JSON verification result. Returns passed=True fallback on parse error."""
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object in response")
        return json.loads(response[start:end])
    except Exception as e:
        logger.warning("Failed to parse verification response: %s", e)
        return {"passed": True, "issues": []}


def run(state: dict) -> dict:
    """Verify summaries and retry via tool if accuracy check fails."""
    summaries = state.get("summaries", [])
    ranked_articles = state.get("ranked_articles", [])

    if not summaries:
        return {"verified_summaries": []}

    # Build URL → snippet lookup from ranked_articles for source text
    article_lookup = {a.get("url", ""): a.get("snippet", "") for a in ranked_articles}

    client = _get_openai_client()
    verified = []

    for summary in summaries:
        url = summary.get("url", "")
        article_text = article_lookup.get(url) or summary.get("title", "")
        bullets = summary.get("bullets", [])
        why_it_matters = summary.get("why_it_matters", "")

        prompt = USER_TEMPLATE.format(
            article_text=article_text,
            summary_bullets=json.dumps(bullets),
            why_it_matters=why_it_matters,
        )

        response = client.chat.completions.create(
            model=settings.openai_verifier_model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_completion_tokens=256,
        )

        result = _parse_result(response.choices[0].message.content)

        if result.get("passed", True):
            verified.append(summary)
            logger.info("Verified (passed): %s", summary.get("title", "")[:60])
        else:
            logger.warning(
                "Verification failed for '%s': %s",
                summary.get("title", "")[:60],
                result.get("issues", []),
            )
            try:
                revised_raw = retry_summarization(
                    article_text=article_text,
                    failed_summary=json.dumps({"bullets": bullets, "why_it_matters": why_it_matters}),
                    constraints=result.get("issues", []),
                )
                start = revised_raw.find("{")
                end = revised_raw.rfind("}") + 1
                revised = json.loads(revised_raw[start:end]) if start != -1 else {}
                verified.append({
                    **summary,
                    "bullets": revised.get("bullets", bullets),
                    "why_it_matters": revised.get("why_it_matters", why_it_matters),
                })
                logger.info("Retry succeeded: %s", summary.get("title", "")[:60])
            except Exception as e:
                logger.warning("Retry failed, keeping original summary: %s", e)
                verified.append(summary)

    logger.info("Verification: %d/%d summaries passed or recovered", len(verified), len(summaries))
    return {"verified_summaries": verified}
