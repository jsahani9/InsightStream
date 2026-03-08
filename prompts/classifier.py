"""Prompt template for the Classifier Agent."""

SYSTEM = """You are a news classification assistant.
Classify each article into exactly one category: AI, FinTech, or Tech."""

USER_TEMPLATE = """
Article title: {title}
Article snippet: {snippet}

Return JSON: {{ "category": "<AI|FinTech|Tech>" }}
"""
