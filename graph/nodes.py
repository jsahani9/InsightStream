"""LangGraph node wrappers.

Each function here wraps an agent/service call and conforms to the
LangGraph node signature: (state: dict) -> dict.
"""


def preference_extraction_node(state: dict) -> dict:
    raise NotImplementedError


def planner_node(state: dict) -> dict:
    raise NotImplementedError


def fetch_articles_node(state: dict) -> dict:
    raise NotImplementedError


def classifier_node(state: dict) -> dict:
    raise NotImplementedError


def deduplication_node(state: dict) -> dict:
    raise NotImplementedError


def ranking_node(state: dict) -> dict:
    raise NotImplementedError


def summarization_node(state: dict) -> dict:
    raise NotImplementedError


def verification_node(state: dict) -> dict:
    raise NotImplementedError


def digest_composition_node(state: dict) -> dict:
    raise NotImplementedError


def email_delivery_node(state: dict) -> dict:
    raise NotImplementedError
