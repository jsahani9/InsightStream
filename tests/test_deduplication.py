from core.constants import RSS_FEED_URLS
from services.article_fetcher import fetch
from services.deduplication import deduplicate

print("=" * 50)
print("Fetching articles...")
articles = fetch(RSS_FEED_URLS)
print(f"Fetched: {len(articles)} articles")

print("=" * 50)
print("Running deduplication...")

try:
    deduped = deduplicate(articles, user_id="test-user")
    print(f"Before: {len(articles)}  After: {len(deduped)}  Removed: {len(articles) - len(deduped)}")

    print("-" * 50)
    print("Sample output (first 3):")
    for i, article in enumerate(deduped[:3], start=1):
        print(f"{i}. {article['title']}")
        print(f"   {article['url']}")
except Exception as e:
    print(f"FAILED: {e}")

print("=" * 50)
