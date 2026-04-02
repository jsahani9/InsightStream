"""Project-wide constants for InsightStream."""

from typing import Final


RSS_FEED_URLS: Final[list[str]] = [
    # ── Tech ──────────────────────────────────────────────────────────────────
    "https://techcrunch.com/feed/",
    "https://venturebeat.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss",
    "https://www.zdnet.com/news/rss.xml",
    "https://www.marktechpost.com/feed/",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://rss.slashdot.org/Slashdot/slashdotMain",
    "https://www.theregister.com/headlines.rss",
    "https://www.engadget.com/rss.xml",
    "https://www.technologyreview.com/feed/",           # MIT Technology Review
    "https://www.fastcompany.com/latest/rss",
    # ── AI ────────────────────────────────────────────────────────────────────
    "https://aiweekly.co/issues.rss",
    "https://www.artificialintelligence-news.com/feed/",
    "https://www.deeplearning.ai/the-batch/feed/",      # DeepLearning.AI
    "https://importai.substack.com/feed",               # Jack Clark's Import AI
    "https://aisnakeoil.substack.com/feed",             # AI research/critique
    # ── FinTech ───────────────────────────────────────────────────────────────
    "https://www.finextra.com/rss/fullnews.aspx",
    "https://finovate.com/feed/",
    "https://www.crowdfundinsider.com/feed/",
    "https://www.pymnts.com/feed/",                     # Payments / FinTech
    # ── Crypto ────────────────────────────────────────────────────────────────
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://bitcoinist.com/feed/",
    # ── Finance / Stocks / Markets ────────────────────────────────────────────
    "https://feeds.marketwatch.com/marketwatch/topstories/",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",   # CNBC Markets
    "https://www.cnbc.com/id/10001147/device/rss/rss.html",    # CNBC Tech
    "https://www.forbes.com/real-time/feed2/",
    "https://feeds.feedburner.com/TheHackerNews",       # Cybersecurity / tech
    # ── World / Business News ─────────────────────────────────────────────────
    "https://feeds.bbci.co.uk/news/business/rss.xml",   # BBC Business
    "https://feeds.bbci.co.uk/news/technology/rss.xml", # BBC Technology
    "https://www.theguardian.com/technology/rss",        # Guardian Tech
    "https://www.theguardian.com/business/rss",          # Guardian Business
]

MAX_ARTICLES_PER_FEED: Final[int] = 10
MAX_SNIPPET_LENGTH: Final[int] = 500


# =========================
# FUTURE EXTENSIONS
# =========================
# (Use later when scaling system)

# MAX_TOTAL_ARTICLES: Final[int] = 150
# REQUEST_TIMEOUT: Final[int] = 10
# USER_AGENT: Final[str] = "InsightStream/1.0"