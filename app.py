"""InsightStream — Streamlit UI

Pages:
    1. Register / Login   — find or create a user by email
    2. Preferences        — set interests, excluded topics, article count
    3. Run Digest         — trigger pipeline, preview HTML digest
    4. History            — view articles sent to the user
"""

import asyncio
import uuid
from datetime import datetime, timezone

import streamlit as st
from sqlalchemy import select, desc

from core.config import settings
from db import session as db_session
from db.models import Article, Preference, SentArticle, User

# ── Async helpers ─────────────────────────────────────────────────────────────

def run(coro):
    """Run an async coroutine from sync Streamlit context.
    Re-initializes the DB engine inside each new event loop to avoid
    'Future attached to a different loop' errors from asyncpg.
    """
    async def _wrapper():
        db_session.init_db(settings.database_url)
        return await coro
    return asyncio.run(_wrapper())


async def _get_user_by_email(email: str) -> User | None:
    async with db_session.AsyncSessionLocal() as s:
        result = await s.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def _create_user(email: str) -> User:
    async with db_session.AsyncSessionLocal() as s:
        user = User(email=email, is_subscribed=True)
        s.add(user)
        await s.commit()
        await s.refresh(user)
        return user


async def _get_preference(user_id: uuid.UUID) -> Preference | None:
    async with db_session.AsyncSessionLocal() as s:
        result = await s.execute(
            select(Preference).where(Preference.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def _upsert_preference(user_id: uuid.UUID, interests: list[str],
                              excluded: list[str], article_count: int) -> None:
    async with db_session.AsyncSessionLocal() as s:
        result = await s.execute(
            select(Preference).where(Preference.user_id == user_id)
        )
        pref = result.scalar_one_or_none()
        if pref is None:
            pref = Preference(user_id=user_id)
            s.add(pref)
        pref.interests = interests
        pref.excluded_topics = excluded
        pref.article_count = article_count
        pref.updated_at = datetime.now(timezone.utc)
        await s.commit()


async def _toggle_subscription(user_id: uuid.UUID, subscribe: bool) -> None:
    async with db_session.AsyncSessionLocal() as s:
        result = await s.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_subscribed = subscribe
            await s.commit()


async def _get_history(user_id: uuid.UUID, limit: int = 30) -> list[dict]:
    async with db_session.AsyncSessionLocal() as s:
        result = await s.execute(
            select(SentArticle, Article)
            .join(Article, SentArticle.article_id == Article.id)
            .where(SentArticle.user_id == user_id)
            .order_by(desc(SentArticle.sent_at))
            .limit(limit)
        )
        rows = result.all()
    return [
        {
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "category": article.category,
            "sent_at": sent.sent_at.strftime("%b %d, %Y %H:%M UTC"),
        }
        for sent, article in rows
    ]


async def _run_pipeline(user_id: str, user_email: str) -> str:
    """Run the full InsightStream pipeline and return the HTML digest."""
    try:
        from graph.pipeline import build_pipeline
    except ImportError:
        raise RuntimeError(
            "Pipeline not available yet — graph/pipeline.py is not implemented. "
            "Aakash needs to finish nodes.py + pipeline.py first."
        )
    pipeline = build_pipeline()
    initial_state = {
        "user_id": user_id,
        "user_email": user_email,
        "raw_preferences": {},
        "structured_preferences": {},
        "fetch_plan": {},
        "raw_articles": [],
        "classified_articles": [],
        "deduplicated_articles": [],
        "ranked_articles": [],
        "summaries": [],
        "verified_summaries": [],
        "digest": "",
    }
    final_state = await pipeline.ainvoke(initial_state)
    return final_state.get("digest", "")

# ── Page: Register / Login ────────────────────────────────────────────────────

def page_login():
    st.title("InsightStream")
    st.caption("Your personalized daily digest for AI, FinTech & Tech news")
    st.divider()

    st.subheader("Get Started")
    email = st.text_input("Enter your email", placeholder="you@example.com").strip().lower()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            if not email:
                st.warning("Please enter an email.")
            else:
                user = run(_get_user_by_email(email))
                if user is None:
                    st.error("No account found. Click Register to create one.")
                else:
                    st.session_state.user_id = str(user.id)
                    st.session_state.user_email = user.email
                    st.session_state.is_subscribed = user.is_subscribed
                    st.session_state.page = "preferences"
                    st.rerun()

    with col2:
        if st.button("Register", use_container_width=True):
            if not email:
                st.warning("Please enter an email.")
            else:
                existing = run(_get_user_by_email(email))
                if existing:
                    st.info("Account already exists — logging you in.")
                    user = existing
                else:
                    user = run(_create_user(email))
                    st.success("Account created!")
                st.session_state.user_id = str(user.id)
                st.session_state.user_email = user.email
                st.session_state.is_subscribed = user.is_subscribed
                st.session_state.page = "preferences"
                st.rerun()

# ── Page: Preferences ─────────────────────────────────────────────────────────

async def _extract_preferences(user_id: str, raw_text: str) -> dict:
    """Run the preference extraction agent on raw user text."""
    from agents import preference_extraction_agent
    db_session.init_db(settings.database_url)
    return await preference_extraction_agent.run({
        "user_id": user_id,
        "text": raw_text,
    })


def page_preferences():
    st.title("Preferences")
    st.caption(f"Logged in as **{st.session_state.user_email}**")
    st.divider()

    uid = uuid.UUID(st.session_state.user_id)
    pref = run(_get_preference(uid))

    # ── Free-text preference input ──────────────────────────────────────────
    st.subheader("Tell us what news you want")
    raw_text = st.text_area(
        "Describe your interests in your own words",
        height=120,
        placeholder=(
            "e.g. I'm a software engineer interested in AI startups, large language models, "
            "and FinTech. I follow the latest research on generative AI and enjoy reading about "
            "venture capital deals. Please avoid crypto, NFTs, and celebrity news."
        ),
    )

    if st.button("Extract Preferences with AI", use_container_width=True):
        if not raw_text.strip():
            st.warning("Please describe your interests first.")
        else:
            with st.spinner("Analyzing your input with Claude..."):
                try:
                    extracted = run(_extract_preferences(st.session_state.user_id, raw_text))
                    st.session_state.extracted_interests = ", ".join(extracted.get("interests", []))
                    st.session_state.extracted_excluded = ", ".join(extracted.get("excluded_topics", []))
                    st.session_state.extracted_count = extracted.get("article_count", 5)
                    st.success("Preferences extracted! Review and adjust below, then save.")
                except Exception as e:
                    st.error(f"Extraction failed: {e}")

    st.divider()

    # ── Structured fields (pre-filled from extraction or existing DB prefs) ─
    existing_interests = st.session_state.pop("extracted_interests", None) \
        or (", ".join(pref.interests) if pref else "")
    existing_excluded = st.session_state.pop("extracted_excluded", None) \
        or (", ".join(pref.excluded_topics) if pref else "")
    existing_count = st.session_state.pop("extracted_count", None) \
        or (pref.article_count if pref else 5)

    st.subheader("Review & adjust")

    interests_raw = st.text_area(
        "Interests (comma-separated)",
        value=existing_interests,
        height=80,
        help="e.g. AI, machine learning, blockchain, startups",
    )

    excluded_raw = st.text_area(
        "Excluded topics (comma-separated, leave blank for none)",
        value=existing_excluded,
        height=68,
        help="e.g. crypto, NFT",
    )

    st.subheader("How many articles per digest?")
    article_count = st.slider("Article count", min_value=1, max_value=15, value=int(existing_count))

    st.divider()
    st.subheader("Daily Digest Subscription")

    currently_subscribed = st.session_state.get("is_subscribed", True)
    subscribed = st.toggle("Subscribe to daily digest", value=currently_subscribed)

    if subscribed:
        st.success("Your digest will be delivered to your inbox every day at **9:00 AM**. Unsubscribe anytime.")
    else:
        st.warning("You are unsubscribed. Toggle on to start receiving daily digests.")

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Save Preferences", use_container_width=True, type="primary"):
            interests = [t.strip() for t in interests_raw.split(",") if t.strip()]
            excluded = [t.strip() for t in excluded_raw.split(",") if t.strip()]
            run(_upsert_preference(uid, interests, excluded, article_count))
            run(_toggle_subscription(uid, subscribed))
            st.session_state.is_subscribed = subscribed
            if subscribed and not currently_subscribed:
                st.success("Subscribed! Your first digest arrives tomorrow at 9:00 AM.")
            elif not subscribed and currently_subscribed:
                st.info("Unsubscribed. You won't receive any more digests.")
            else:
                st.success("Preferences saved!")

    with col2:
        if st.button("Run Digest →", use_container_width=True):
            st.session_state.page = "digest"
            st.rerun()

# ── Page: Run Digest ──────────────────────────────────────────────────────────

def page_digest():
    st.title("Run Digest")
    st.caption(f"Logged in as **{st.session_state.user_email}**")
    st.divider()

    st.info(
        "This will run the full InsightStream pipeline: fetch articles → classify → "
        "deduplicate → rank → summarize → verify → compose digest → send email."
    )

    if st.button("Run Now", type="primary", use_container_width=True):
        with st.spinner("Running pipeline — this may take 1–2 minutes..."):
            try:
                digest_html = run(_run_pipeline(
                    st.session_state.user_id,
                    st.session_state.user_email,
                ))
                st.session_state.last_digest = digest_html
                st.success("Done! Digest generated and sent to your email.")
            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Pipeline error: {e}")

    if st.session_state.get("last_digest"):
        st.divider()
        st.subheader("Preview")
        st.components.v1.html(st.session_state.last_digest, height=700, scrolling=True)

# ── Page: History ─────────────────────────────────────────────────────────────

def page_history():
    st.title("Article History")
    st.caption(f"Logged in as **{st.session_state.user_email}**")
    st.divider()

    uid = uuid.UUID(st.session_state.user_id)
    history = run(_get_history(uid))

    if not history:
        st.info("No articles sent yet. Run a digest first.")
        return

    st.caption(f"Showing last {len(history)} articles delivered to you.")

    for item in history:
        with st.container():
            cat = item["category"] or "General"
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**[{item['title']}]({item['url']})**")
                st.caption(f"{item['source']} · {item['sent_at']}")
            with col2:
                st.markdown(
                    f"<span style='background:#e8f0fe;color:#1a73e8;padding:2px 8px;"
                    f"border-radius:12px;font-size:12px;'>{cat}</span>",
                    unsafe_allow_html=True,
                )
            st.divider()

# ── Sidebar navigation ────────────────────────────────────────────────────────

def sidebar():
    with st.sidebar:
        st.markdown("## InsightStream")
        st.markdown("---")

        if "user_email" in st.session_state:
            st.markdown(f"**{st.session_state.user_email}**")
            st.caption("User ID: " + st.session_state.user_id[:8] + "...")
            st.markdown("---")

            if st.button("Preferences", use_container_width=True):
                st.session_state.page = "preferences"
                st.rerun()
            if st.button("Run Digest", use_container_width=True):
                st.session_state.page = "digest"
                st.rerun()
            if st.button("History", use_container_width=True):
                st.session_state.page = "history"
                st.rerun()

            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                for key in ["user_id", "user_email", "is_subscribed", "page", "last_digest"]:
                    st.session_state.pop(key, None)
                st.rerun()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="InsightStream",
        page_icon="📰",
        layout="centered",
    )

    sidebar()

    page = st.session_state.get("page", "login")

    if "user_id" not in st.session_state:
        page_login()
    elif page == "preferences":
        page_preferences()
    elif page == "digest":
        page_digest()
    elif page == "history":
        page_history()
    else:
        page_preferences()


if __name__ == "__main__":
    main()
