"""Summarization Agent.

Generates concise bullet-point summaries with "why it matters" context
for each ranked article.
Model: Claude Sonnet 4.5 via AWS Bedrock.
"""

SYSTEM = """You are a technical news summarization assistant.
Summarize each article into 2–3 concise bullet points followed by a "Why it matters" sentence."""

USER_TEMPLATE = """
Article title: {title}
Article text: {text}

Return JSON: {{ "bullets": list[str], "why_it_matters": str }}
"""


def run(state: dict) -> dict:
    """Summarize ranked articles into digest-ready insights."""
    raise NotImplementedError
