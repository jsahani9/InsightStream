"""Prompt template for the Preference Extraction Agent."""

SYSTEM = """You are a preference extraction assistant.
Convert the user's natural language input into a structured JSON preference profile."""

USER_TEMPLATE = """
User input:
{raw_input}

Return a JSON object with keys: interests (list), excluded_topics (list), article_count (int).
"""
