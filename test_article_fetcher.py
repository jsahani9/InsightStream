from core.constants import RSS_FEED_URLS
from services.article_fetcher import fetch

FEEDS = RSS_FEED_URLS

print("=" * 50)
print("Test 1: fetch from real RSS feeds")

try:
    articles = fetch(FEEDS)
    print(f"Success. Articles fetched: {len(articles)}")

    for i, article in enumerate(articles[:3], start=1):
        print("-" * 50)
        print(f"{i}. {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Snippet: {article['snippet'][:100]}...")
        print(f"Published: {article['published_at']}")
        print(f"Source: {article['source_url']}")
except Exception as e:
    print(f"FAILED: {e}")

print("=" * 50)
print("Test 2: empty sources list")

result = fetch([])
print(f"Empty input returned: {result}")

print("=" * 50)
print("Test 3: invalid URL (should not crash)")

result = fetch(["https://this-url-does-not-exist-xyz.com/feed"])
print(f"Invalid URL returned: {result}")

print("=" * 50)
