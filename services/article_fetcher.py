"""Article fetcher service.

Fetches articles from RSS/Atom feeds.
Returns a list of raw article dicts: {title, url, snippet, published_at, source_url}
"""

import logging
import re
import time
from html.parser import HTMLParser

import feedparser
import httpx

from core.constants import MAX_ARTICLES_PER_FEED, MAX_SNIPPET_LENGTH

MAX_CONTENT_LENGTH = 3000


class _TextExtractor(HTMLParser):
    """Extracts plain text from HTML.

    Prefers content inside <article> or <main> tags when present.
    Falls back to all body text (minus script/style/nav/header/footer/aside) if not found.
    """

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = False
        self._article_depth = 0   # depth inside <article> or <main>
        self._in_article = False
        self._found_article = False

    def handle_starttag(self, tag: str, _attrs: list) -> None:
        if tag in ("article", "main"):
            self._article_depth += 1
            self._in_article = True
            self._found_article = True
        if tag in ("script", "style", "nav", "header", "footer", "aside"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("article", "main"):
            self._article_depth -= 1
            if self._article_depth == 0:
                self._in_article = False
        if tag in ("script", "style", "nav", "header", "footer", "aside"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        # If the page has article/main tags, only keep text from within them
        if self._found_article and not self._in_article:
            return
        stripped = data.strip()
        if stripped:
            self._parts.append(stripped)

    def get_text(self) -> str:
        return " ".join(self._parts)

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


def enrich_with_content(articles: list[dict]) -> list[dict]:
    """Fetch full article text for each article and add a 'content' field.

    Falls back to snippet if the page cannot be fetched or parsed.
    Only fetches URLs not already enriched.
    """
    enriched = []
    for article in articles:
        url = article.get("url", "")
        if not url:
            enriched.append(article)
            continue
        try:
            response = httpx.get(
                url,
                timeout=10,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"},
            )
            response.raise_for_status()
            extractor = _TextExtractor()
            extractor.feed(response.text)
            content = extractor.get_text()[:MAX_CONTENT_LENGTH]
            enriched.append({**article, "content": content or article.get("snippet", "")})
            logger.info("Fetched content for: %s", article.get("title", "")[:60])
        except Exception as e:
            logger.warning("Could not fetch content for %s: %s", url, e)
            enriched.append({**article, "content": article.get("snippet", "")})
    return enriched
