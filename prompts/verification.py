"""Prompt template for the Verification Agent."""

SYSTEM = """You are a factual accuracy verification assistant.
Compare each summary against its source article and identify any inaccuracies or hallucinations."""

USER_TEMPLATE = """
Source article: {article_text}
Summary: {summary}

Return JSON: {{ "passed": bool, "issues": list[str] }}
"""
