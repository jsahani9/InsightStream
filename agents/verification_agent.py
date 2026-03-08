"""Verification Agent.

Cross-checks each summary against its source article for factual accuracy.
If a summary fails, triggers the summarization retry tool with stricter constraints.
Model: GPT-5.2 via OpenAI.
"""


def run(state: dict) -> dict:
    """Verify summaries and retry via tool if accuracy check fails."""
    raise NotImplementedError
