"""Preference Extraction Agent.

Converts raw user input (interests, excluded topics, article count)
into a structured preference object stored in the database.
Model: Claude Sonnet 4.5 via AWS Bedrock.
"""

SYSTEM = """You are a preference extraction assistant.
Convert the user's natural language input into a structured JSON preference profile."""

USER_TEMPLATE = """
User input:
{raw_input}

Return a JSON object with keys: interests (list), excluded_topics (list), article_count (int).
"""


def run(user_input: dict) -> dict:
    """Extract structured preferences from raw user input."""
    raise NotImplementedError
