"""Web Search Tool.

Used by the Planner Agent to discover trending topics and dynamic sources.
Input:  query (str), max_results (int)
Output: list of {title, url, snippet, published_at}
"""


def web_search(query: str, max_results: int = 10) -> list[dict]:
    """Search the web and return structured results."""
    raise NotImplementedError
