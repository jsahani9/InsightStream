"""Planner Agent.

Uses user preferences from the DB and web search to generate a fetch plan
with source priorities and category weights for the day's digest.
Model: OpenAI planner model.

Flow:
  1. Read structured preferences from DB via get_user_preferences().
  2. Read recently sent article IDs via get_recently_sent_articles()
     so the plan avoids repeating topics the user already saw.
  3. Search trending topics per interest using the web search tool.
  4. Ask OpenAI to produce a JSON fetch plan (sources + category weights).
"""

import json
import logging

from openai import OpenAI

from core.config import settings
from tools.database_query_tool import get_recently_sent_articles, get_user_preferences
from tools.web_search_tool import web_search

logger = logging.getLogger(__name__)

_openai_client = None

SYSTEM = """You are a news planning assistant.
Given user preferences, recently sent article IDs to avoid, and today's trending topics,
decide which sources to fetch and how to weight topic categories."""

USER_TEMPLATE = """
User preferences:
{preferences}

Recently sent article IDs (avoid repeating these topics):
{recently_sent}

Trending topics from web search:
{trending}

You MUST only pick sources from this approved list (confirmed working RSS feeds):

AI / Machine Learning:
- https://www.marktechpost.com/feed/
- https://www.artificialintelligence-news.com/feed/
- https://venturebeat.com/feed/
- https://www.deeplearning.ai/the-batch/feed/
- https://importai.substack.com/feed

Tech / Software / Cybersecurity:
- https://techcrunch.com/feed/
- https://www.theverge.com/rss/index.xml
- https://www.wired.com/feed/rss
- https://www.zdnet.com/news/rss.xml
- https://feeds.arstechnica.com/arstechnica/index
- https://www.theregister.com/headlines.rss
- https://www.engadget.com/rss.xml
- https://www.technologyreview.com/feed/
- https://feeds.feedburner.com/TheHackerNews

FinTech / Payments / Banking:
- https://www.finextra.com/rss/fullnews.aspx
- https://finovate.com/feed/
- https://www.crowdfundinsider.com/feed/
- https://www.pymnts.com/feed/

Crypto / Blockchain / Web3:
- https://www.coindesk.com/arc/outboundfeeds/rss/
- https://cointelegraph.com/rss
- https://decrypt.co/feed
- https://bitcoinist.com/feed/

Markets / Finance / Stocks:
- https://feeds.marketwatch.com/marketwatch/topstories/
- https://www.cnbc.com/id/100003114/device/rss/rss.html
- https://www.cnbc.com/id/10001147/device/rss/rss.html
- https://www.forbes.com/real-time/feed2/

World / Business News:
- https://feeds.bbci.co.uk/news/business/rss.xml
- https://feeds.bbci.co.uk/news/technology/rss.xml
- https://www.theguardian.com/technology/rss
- https://www.theguardian.com/business/rss

Pick sources that best match the user's interests and categories. Include at least one source per user interest category for diversity.

Return ONLY a valid JSON object with exactly these keys:
- sources          (list of URLs picked from the approved list above)
- category_weights (dict mapping each user category to a float weight 0.0–1.0)

Example:
{{"sources": ["https://techcrunch.com/feed/", "https://www.coindesk.com/arc/outboundfeeds/rss/", "https://feeds.marketwatch.com/marketwatch/topstories/"], "category_weights": {{"Tech": 0.4, "Crypto": 0.3, "Markets": 0.3}}}}
"""


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _parse_fetch_plan(response: str) -> dict:
    """Extract JSON fetch plan from OpenAI response. Returns empty fallback on failure."""
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object in response")
        return json.loads(response[start:end])
    except Exception as e:
        logger.warning("Failed to parse fetch plan: %s", e)
        return {"sources": [], "category_weights": {}}

""" 
 Before it didn't know for what it's planning, now with the user_id it has clear direction.
 Now it knows for what user it's producing the ouput. 

    - knows which user it's planning for
    - reads preferences from DB
    - Avoids topics user already saw
    - Uses correct interests key
    - can run Async DB calls
    
"""
async def run(state: dict) -> dict:
    """Plan fetch strategy based on user preferences and trending topics.

    Reads preferences and recently sent articles from the DB so the plan
    is always up-to-date and avoids re-delivering known content.
    """
    user_id: str = state.get("user_id", "")

    # Step 1: load preferences from DB; fall back to pipeline state if missing
    db_preferences = {}
    if user_id:
        db_preferences = await get_user_preferences(user_id)
        if db_preferences:
            logger.info("Planner: loaded preferences from DB for user %s", user_id)
        else:
            logger.warning(
                "Planner: no DB preferences for user %s, falling back to state", user_id
            )

    preferences = db_preferences or state.get("structured_preferences", {})
    interests: list[str] = preferences.get("interests", [])

    # Step 2: load recently sent article IDs to avoid topic repetition
    recently_sent: list[str] = []
    if user_id:
        recently_sent = await get_recently_sent_articles(user_id, days=7)
        logger.info(
            "Planner: %d recently sent articles found for user %s",
            len(recently_sent), user_id,
        )

    # Step 3: search for trending topics per interest
    web_articles: list[dict] = []
    trending_lines: list[str] = []

    for interest in interests:
        results = web_search(query=f"latest {interest} news today", max_results=5)
        for r in results:
            web_articles.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", ""),
                "published_at": r.get("published_at", ""),
                "source_url": r.get("url", ""),
            })
        titles = [r["title"] for r in results[:3]]
        trending_lines.append(f"{interest}: {', '.join(titles)}")

    trending_text = "\n".join(trending_lines) if trending_lines else "No trending data available."

    # Step 4: ask OpenAI to produce the fetch plan
    prompt = USER_TEMPLATE.format(
        preferences=json.dumps(preferences, indent=2),
        recently_sent=json.dumps(recently_sent) if recently_sent else "none",
        trending=trending_text,
    )

    client = _get_openai_client()
    response = client.chat.completions.create(
        model=settings.openai_planner_model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_completion_tokens=512,
    )

    raw_response = response.choices[0].message.content
    fetch_plan = _parse_fetch_plan(raw_response)

    logger.info(
        "Planner: %d web articles fetched across %d interests", len(web_articles), len(interests)
    )

    return {
        "fetch_plan": fetch_plan,
        "raw_articles": web_articles,
        "structured_preferences": preferences,
    }
