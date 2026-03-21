from core.constants import RSS_FEED_URLS
from services.article_fetcher import fetch
from services.deduplication import deduplicate
from agents.ranking_agent import run

print("=" * 50)
print("Fetching and deduplicating articles...")
articles = fetch(RSS_FEED_URLS)
deduped = deduplicate(articles, user_id="test-user")
print(f"Fetched: {len(articles)}  After dedup: {len(deduped)}")

print("=" * 50)
print("Running ranking agent...")

state = {
    "deduplicated_articles": deduped,
    "structured_preferences": {
        "topics": ["AI", "FinTech", "Tech"],
        "sources": ["TechCrunch", "VentureBeat"],
    },
}

try:
    result = run(state)
    ranked = result["ranked_articles"]
    print(f"Top {len(ranked)} articles:")
    print("-" * 50)
    for i, article in enumerate(ranked, start=1):
        print(f"{i}. [{article.get('score', '?')}] {article['title']}")
        print(f"   {article['url']}")
except Exception as e:
    print(f"FAILED: {e}")

print("=" * 50)
