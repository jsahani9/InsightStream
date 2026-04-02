from core.constants import RSS_FEED_URLS
from services.article_fetcher import fetch
from services.deduplication import deduplicate
from agents.ranking_agent import run as rank
from agents.summarization_agent import run as summarize
from agents.verification_agent import run as verify

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

summarized = summarize(ranked)
print(f"Summarized: {len(summarized['summaries'])} articles")

print("=" * 50)
print("Running verification agent...")

try:
    full_state = {**ranked, **summarized}
    result = verify(full_state)
    verified = result["verified_summaries"]
    print(f"Verified: {len(verified)}/{len(summarized['summaries'])} summaries passed or recovered")
    print("-" * 50)
    for s in verified:
        print(f"\n[{s.get('score', '?')}] {s['title']}")
        for bullet in s.get("bullets", []):
            print(f"  • {bullet}")
        print(f"  Why it matters: {s.get('why_it_matters', '')}")
except Exception as e:
    print(f"FAILED: {e}")

print("=" * 50)
