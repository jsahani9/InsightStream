"""Article fetcher.

Retrieves articles from RSS feeds and dynamically discovered sources.
Returns a list of raw article dicts for downstream processing.
"""


def fetch(sources: list[str]) -> list[dict]:
    """Fetch articles from the given source URLs."""
    raise NotImplementedError
