"""Preference Extraction Agent.

Converts raw user input (interests, excluded topics, article count)
into a structured preference object stored in the database.
Model: Claude Sonnet 4.5 via AWS Bedrock.
"""


def run(user_input: dict) -> dict:
    """Extract structured preferences from raw user input."""
    raise NotImplementedError
