"""Summarization Retry Tool.

Called by the Verification Agent when a summary fails accuracy checks.
Triggers re-summarization with stricter constraints.
Input:  article_text (str), failed_summary (str), constraints (list[str])
Output: revised_summary (str)
"""


def retry_summarization(
    article_text: str,
    failed_summary: str,
    constraints: list[str],
) -> str:
    """Re-summarize an article under stricter accuracy constraints."""
    raise NotImplementedError
