from core.constants import RSS_FEED_URLS
from services.article_fetcher import fetch
from services.deduplication import deduplicate
from agents.ranking_agent import run as rank
from agents.summarization_agent import run as summarize

print("=" * 50)
print("Fetching and ranking articles...")
articles = fetch(RSS_FEED_URLS)
deduped = deduplicate(articles, user_id="test-user")

state = {
    "deduplicated_articles": deduped,
    "structured_preferences": {
        "topics": ["AI", "FinTech", "Tech"],
        "sources": ["TechCrunch", "VentureBeat"],
    },
}

ranked = rank(state)
print(f"Ranked: {len(ranked['ranked_articles'])} articles")

print("=" * 50)
print("Running summarization agent...")

try:
    result = summarize(ranked)
    summaries = result["summaries"]
    print(f"Summarized: {len(summaries)} articles")
    print("-" * 50)
    for s in summaries:
        print(f"\n[{s.get('score', '?')}] {s['title']}")
        for bullet in s.get("bullets", []):
            print(f"  • {bullet}")
        print(f"  Why it matters: {s.get('why_it_matters', '')}")
except Exception as e:
    print(f"FAILED: {e}")

print("=" * 50)
