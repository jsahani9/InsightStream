"""Verification Agent.

Cross-checks each summary against its source article for factual accuracy.
If a summary fails, triggers the summarization retry tool with stricter constraints.
Model: GPT-5.2 via OpenAI.
"""

SYSTEM = """You are a factual accuracy verification assistant.
Compare each summary against its source article and identify any inaccuracies or hallucinations."""

USER_TEMPLATE = """
Source article: {article_text}
Summary: {summary}

Return JSON: {{ "passed": bool, "issues": list[str] }}
"""


def run(state: dict) -> dict:
    """Verify summaries and retry via tool if accuracy check fails."""
    raise NotImplementedError
