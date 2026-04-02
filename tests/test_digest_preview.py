"""Test digest preview — runs full pipeline up to digest composition, no email sent."""

import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
)

from core.config import settings
from db.session import init_db
from agents import (
    preference_extraction_agent,
    planner_agent,
    classifier_agent,
    ranking_agent,
    summarization_agent,
    verification_agent,
)
from services import article_fetcher, deduplication, digest_composition
from core.constants import RSS_FEED_URLS

USER_ID    = "d5668025-dc5c-4540-994f-2e7b2fe3c7ff"
USER_EMAIL = "jasveen1800@gmail.com"
RAW_TEXT   = "I'm interested in AI, machine learning, FinTech, and tech startups. Exclude crypto and NFT. Send me 5 articles."


async def main():
    init_db(settings.database_url)

    state = {
        "user_id": USER_ID,
        "user_email": USER_EMAIL,
        "raw_preferences": {"text": RAW_TEXT},
        "structured_preferences": {},
        "fetch_plan": {},
        "raw_articles": [],
        "classified_articles": [],
        "deduplicated_articles": [],
        "ranked_articles": [],
        "summaries": [],
        "verified_summaries": [],
        "digest": "",
        "fetch_retry_count": 0,
        "summarization_retry_count": 0,
        "pipeline_status": "",
        "on_demand": True,
        "skip_email": True,
    }

    # Step 1 — Preference extraction
    print("\n── Step 1: Preference Extraction ──")
    result = await preference_extraction_agent.run({
        "user_id": USER_ID,
        "text": RAW_TEXT,
    })
    state["structured_preferences"] = result
    print(f"Interests: {result.get('interests')}")
    print(f"Excluded:  {result.get('excluded_topics')}")
    print(f"Count:     {result.get('article_count')}")

    # Step 2 — Planner (web search)
    print("\n── Step 2: Planner ──")
    planner_result = await planner_agent.run(state)
    state["fetch_plan"] = planner_result.get("fetch_plan", {})
    state["raw_articles"] = planner_result.get("raw_articles", [])
    state["structured_preferences"] = planner_result.get("structured_preferences", state["structured_preferences"])
    print(f"Web articles from planner: {len(state['raw_articles'])}")

    # Step 3 — Fetch RSS
    print("\n── Step 3: Fetch RSS Articles ──")
    sources = state["fetch_plan"].get("sources") or RSS_FEED_URLS
    rss_articles = article_fetcher.fetch(sources)
    state["raw_articles"] = state["raw_articles"] + rss_articles
    print(f"Total after RSS merge: {len(state['raw_articles'])}")

    # Step 4 — Classifier
    print("\n── Step 4: Classifier ──")
    result = classifier_agent.run(state)
    state["classified_articles"] = result.get("classified_articles", [])
    print(f"Classified: {len(state['classified_articles'])}")

    # Step 5 — Deduplication
    print("\n── Step 5: Deduplication ──")
    state["deduplicated_articles"] = await deduplication.deduplicate(
        state["classified_articles"], USER_ID
    )
    print(f"After dedup: {len(state['deduplicated_articles'])}")

    if not state["deduplicated_articles"]:
        print("No articles after dedup — try clearing sent_articles table.")
        return

    # Step 6 — Ranking
    print("\n── Step 6: Ranking ──")
    result = ranking_agent.run(state)
    state["ranked_articles"] = result.get("ranked_articles", [])
    print(f"Top ranked: {len(state['ranked_articles'])}")
    for i, a in enumerate(state["ranked_articles"], 1):
        print(f"  {i}. {a.get('title', '')[:80]}")

    # Step 6.5 — Enrich with full content + drop thin articles
    print("\n── Step 6.5: Content Enrichment + Filter ──")
    state["ranked_articles"] = article_fetcher.enrich_with_content(state["ranked_articles"])
    before = len(state["ranked_articles"])
    state["ranked_articles"] = [
        a for a in state["ranked_articles"]
        if len(a.get("content") or a.get("snippet", "")) >= 300
    ]
    print(f"Dropped {before - len(state['ranked_articles'])} thin articles, {len(state['ranked_articles'])} remaining")

    # Step 7 — Summarization
    print("\n── Step 7: Summarization ──")
    result = summarization_agent.run(state)
    state["summaries"] = result.get("summaries", [])
    print(f"Summaries generated: {len(state['summaries'])}")

    # Step 8 — Verification
    print("\n── Step 8: Verification ──")
    result = verification_agent.run(state)
    verified = result.get("verified_summaries", [])
    # Trim to exactly what user requested
    article_count = state["structured_preferences"].get("article_count", 5)
    if len(verified) > article_count:
        verified = verified[:article_count]
    state["verified_summaries"] = verified
    print(f"Verified summaries: {len(state['verified_summaries'])} / {article_count} requested")

    # Step 9 — Digest composition
    print("\n── Step 9: Digest Composition ──")
    digest_html = digest_composition.compose(
        verified_summaries=state["verified_summaries"],
        user_preferences=state["structured_preferences"],
    )
    state["digest"] = digest_html

    # ── Print summaries to terminal ───────────────────────────────────────────
    print("\n" + "═" * 70)
    print("DIGEST PREVIEW (no email sent)")
    print("═" * 70)
    for i, s in enumerate(state["verified_summaries"], 1):
        print(f"\n{i}. {s.get('title', '')}")
        print(f"   URL: {s.get('url', '')}")
        for b in s.get("bullets", []):
            print(f"   • {b}")
        print(f"   WHY IT MATTERS: {s.get('why_it_matters', '')}")

    # Save HTML preview to file
    with open("digest_preview.html", "w") as f:
        f.write(digest_html)
    print("\n✓ HTML saved to digest_preview.html — open in browser to preview.")
    print("✓ No email was sent.")


if __name__ == "__main__":
    asyncio.run(main())
