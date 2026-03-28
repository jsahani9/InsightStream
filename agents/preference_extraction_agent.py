"""Preference Extraction Agent.

Converts raw user input (interests, excluded topics, article count)
into a structured preference object stored in the database.
Model: Claude Sonnet 4.5 via AWS Bedrock.

Flow:
  1. Send raw user input to Claude → get structured JSON back.
  2. Upsert the structured preference into the `preferences` table.
  3. Return the structured preference dict to the pipeline state.
"""

import json
import logging
import uuid

from sqlalchemy import select

from core.bedrock_client import invoke_claude
from db import session as db_session
from db.models import Preference

logger = logging.getLogger(__name__)

SYSTEM = """You are a preference extraction assistant.
Convert the user's natural language input into a structured JSON preference profile."""

USER_TEMPLATE = """
User input:
{raw_input}

Return ONLY a valid JSON object with exactly these keys:
- interests        (list of strings)
- excluded_topics  (list of strings)
- article_count    (integer, default 10 if not specified)

Example:
{{"interests": ["AI", "FinTech"], "excluded_topics": ["crypto"], "article_count": 5}}
"""


def _parse_llm_response(text: str) -> dict:
    """Extract and validate the JSON object from the model's response. 
       It also validates and normalises the threee required fields
       
    """
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError(f"No JSON object found in model response: {text!r}")
    parsed = json.loads(text[start:end])
    return {
        "interests": list(parsed.get("interests", [])),
        "excluded_topics": list(parsed.get("excluded_topics", [])),
        "article_count": int(parsed.get("article_count", 10)),
    }


async def run(user_input: dict) -> dict:
    """Extract structured preferences from raw user input and persist to DB.

    Args:
        user_input: dict with keys:
            - user_id  (str)  — UUID of the user
            - text     (str)  — free-text preference description from the user

    Returns:
        The structured preference dict that was saved.
    """
    user_id_str: str = user_input["user_id"]
    raw_text: str = user_input.get("text", "")

    # Step 1: call Claude to extract structured preferences
    prompt = USER_TEMPLATE.format(raw_input=raw_text)
    response_text = invoke_claude(prompt=prompt, system=SYSTEM, max_tokens=512, temperature=0.2)
    logger.debug("Claude raw response: %s", response_text)

    structured = _parse_llm_response(response_text)
    logger.info(
        "Extracted preferences for user %s: %s", user_id_str, structured
    )

    # Step 2: upsert into the preferences table
    if db_session.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    uid = uuid.UUID(user_id_str)

    async with db_session.AsyncSessionLocal() as session:
        existing = await session.execute(
            select(Preference).where(Preference.user_id == uid)
        )
        pref = existing.scalar_one_or_none()

        if pref is None:
            pref = Preference(
                user_id=uid,
                interests=structured["interests"],
                excluded_topics=structured["excluded_topics"],
                article_count=structured["article_count"],
                extra={},
            )
            session.add(pref)
            logger.info("Created new preference row for user %s", user_id_str)
        else:
            pref.interests = structured["interests"]
            pref.excluded_topics = structured["excluded_topics"]
            pref.article_count = structured["article_count"]
            logger.info("Updated existing preference row for user %s", user_id_str)

        await session.commit()

    # Step 3: return the structured preference to the pipeline
    return {
        "user_id": user_id_str,
        **structured,
    }
