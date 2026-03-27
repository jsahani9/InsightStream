"""Summarization Retry Tool.

Called by the Verification Agent when a summary fails accuracy checks.
Re-summarizes the article using Claude Sonnet 4.5 via Bedrock with stricter
constraints derived from the verification issues.
Input:  article_text (str), failed_summary (str), constraints (list[str])
Output: revised_summary (str) — JSON string: {"bullets": list[str], "why_it_matters": str}
"""

import logging

from core.bedrock_client import invoke_claude

logger = logging.getLogger(__name__)

SYSTEM = """You are a strict technical news summarization assistant.
You must summarize ONLY based on what is explicitly stated in the source article.
Do not infer, speculate, or add any information not directly present in the source text."""

USER_TEMPLATE = """
Source article: {article_text}

Previous summary (contains errors): {failed_summary}

Issues found in the previous summary — you MUST fix all of these:
{constraints_list}

Rewrite the summary strictly from the source article only. Fix every listed issue.
Do not repeat any of the errors above.

Return JSON: {{ "bullets": list[str], "why_it_matters": str }}
"""


def retry_summarization(
    article_text: str,
    failed_summary: str,
    constraints: list[str],
) -> str:
    """Re-summarize an article under stricter accuracy constraints."""
    constraints_list = "\n".join(f"- {c}" for c in constraints)

    prompt = USER_TEMPLATE.format(
        article_text=article_text,
        failed_summary=failed_summary,
        constraints_list=constraints_list,
    )

    result = invoke_claude(prompt=prompt, system=SYSTEM, max_tokens=512, temperature=0.1)
    logger.info("Retry summarization completed (%d constraints applied)", len(constraints))
    return result
