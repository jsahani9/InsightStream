"""Article fetcher service.

Fetches articles from RSS/Atom feeds.
Returns a list of raw article dicts: {title, url, snippet, published_at, source_url}
"""

import logging
import re
import time

import feedparser
import httpx

from core.constants import MAX_ARTICLES_PER_FEED, MAX_SNIPPET_LENGTH

logger = logging.getLogger(__name__)


def fetch(sources: list[str]) -> list[dict]:
    """Fetch articles from the given RSS/Atom feed URLs."""
    all_articles = []

    for source_url in sources:
        try:
            response = httpx.get(source_url, timeout=10, follow_redirects=True)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
                title = entry.get("title", "").strip()
                url = entry.get("link", "")

                if not title or not url:
                    continue

                snippet = entry.get("summary", "") or ""
                if not snippet and entry.get("content"):
                    snippet = entry.content[0].get("value", "")
                snippet = re.sub(r"<[^>]+>", "", snippet).strip()[:MAX_SNIPPET_LENGTH]

                published_at = ""
                if entry.get("published_parsed"):
                    published_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", entry.published_parsed)
                elif entry.get("published"):
                    published_at = entry.published

                all_articles.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "published_at": published_at,
                    "source_url": source_url,
                })

        except Exception as e:
            logger.warning("Failed to fetch %s: %s", source_url, e)

    return all_articles
