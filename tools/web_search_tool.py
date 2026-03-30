"""Web Search Tool.

Used by the Planner Agent to discover trending topics and dynamic sources.
Input: query (str), max_results (int)
Output: list of {title, url, snippet, published_at}
"""

import httpx
from core.config import settings

SERPER_URL = "https://google.serper.dev/news"


def web_search(query: str, max_results: int = 10) -> list[dict]:
    headers = {
        "X-API-KEY": settings.serper_api_key,
        "Content-Type": "application/json",
    }

    payload = {
        "q": query,
        "num": max_results,
        "tbs": "qdr:d",  # last 24 hours only
    }

    response = httpx.post(
        SERPER_URL,
        headers=headers,
        json=payload,
        timeout=20.0,
    )
    response.raise_for_status()

    data = response.json()
    results = []

    for item in data.get("news", [])[:max_results]:
        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "published_at": item.get("date", ""),
            }
        )

    return results