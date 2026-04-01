"""Project-wide constants for InsightStream."""

from typing import Final


RSS_FEED_URLS: Final[list[str]] = [
    # Tech
    "https://techcrunch.com/feed/",
    "https://venturebeat.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.zdnet.com/news/rss.xml",
    "https://www.marktechpost.com/feed/",
    # AI
    "https://aiweekly.co/issues.rss",
    "https://www.artificialintelligence-news.com/feed/",
    # FinTech / Finance
    "https://www.finextra.com/rss/fullnews.aspx",
    "https://feeds.feedburner.com/TheHackerNews",  # cybersecurity / tech overlap
    # General tech news (open, no paywall)
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://rss.slashdot.org/Slashdot/slashdotMain",
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