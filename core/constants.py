"""Project-wide constants for InsightStream."""

from typing import Final


RSS_FEED_URLS: Final[list[str]] = [
    "https://techcrunch.com/feed/",
    "https://venturebeat.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.finextra.com/rss/fullnews.aspx",
    "https://www.marktechpost.com/feed/",
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.wired.com/feed/rss",
    "https://www.zdnet.com/news/rss.xml",
]

MAX_ARTICLES_PER_FEED: Final[int] = 20
MAX_SNIPPET_LENGTH: Final[int] = 500


# =========================
# FUTURE EXTENSIONS
# =========================
# (Use later when scaling system)

# MAX_TOTAL_ARTICLES: Final[int] = 150
# REQUEST_TIMEOUT: Final[int] = 10
# USER_AGENT: Final[str] = "InsightStream/1.0"