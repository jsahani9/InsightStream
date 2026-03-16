"""Classifier Agent.

Labels each fetched article into a category: AI, FinTech, or Tech.
Model: Llama 3.3 70B via AWS Bedrock.
"""

SYSTEM = """You are a news classification assistant.
Classify each article into exactly one category: AI, FinTech, or Tech."""

USER_TEMPLATE = """
Article title: {title}
Article snippet: {snippet}

Return JSON: {{ "category": "<AI|FinTech|Tech>" }}
"""


def run(state: dict) -> dict:
    """Classify articles by topic category."""
    raise NotImplementedError
