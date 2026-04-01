"""InsightStream — Streamlit UI

Flow:
    1. Login / Register
    2. Dashboard — preferences + subscribe/unsubscribe + get news now + history
"""

import asyncio
import uuid
from datetime import datetime, timezone

import streamlit as st
from sqlalchemy import select, desc

from core.config import settings
from db import session as db_session
from db.models import Article, Preference, SentArticle, User

# ── Theme CSS ─────────────────────────────────────────────────────────────────

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp {
    background: #0a0a0f;
    color: #e2e8f0;
}

/* Hide default streamlit header/footer */
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f0f1a;
    border-right: 1px solid #1e1e3a;
}
[data-testid="stSidebar"] * { color: #a0aec0 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] strong { color: #e2e8f0 !important; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6c63ff, #4facfe);
    color: white !important;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    letter-spacing: 0.3px;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(108, 99, 255, 0.4);
}

/* Secondary buttons in sidebar */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid #2d2d5e !important;
    color: #a0aec0 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #6c63ff !important;
    color: #e2e8f0 !important;
    box-shadow: none;
}

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #13131f !important;
    border: 1px solid #2d2d5e !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6c63ff !important;
    box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.2) !important;
}

/* Slider */
.stSlider > div > div > div { background: #6c63ff !important; }

/* Toggle */
.stCheckbox > label > span { color: #a0aec0 !important; }

/* Alert boxes */
.stSuccess { background: rgba(72, 199, 142, 0.1) !important; border: 1px solid rgba(72, 199, 142, 0.3) !important; border-radius: 10px !important; }
.stWarning { background: rgba(255, 171, 0, 0.1) !important; border: 1px solid rgba(255, 171, 0, 0.3) !important; border-radius: 10px !important; }
.stError   { background: rgba(255, 82, 82, 0.1) !important;  border: 1px solid rgba(255, 82, 82, 0.3) !important;  border-radius: 10px !important; }
.stInfo    { background: rgba(79, 172, 254, 0.1) !important; border: 1px solid rgba(79, 172, 254, 0.3) !important; border-radius: 10px !important; }

/* Divider */
hr { border-color: #1e1e3a !important; }

/* Labels */
label, .stSlider label { color: #a0aec0 !important; font-size: 13px !important; }

/* Spinner */
.stSpinner > div { border-top-color: #6c63ff !important; }
</style>
"""

# ── Async helpers ─────────────────────────────────────────────────────────────

def run(coro):
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
        user = User(email=email, is_subscribed=False)
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


async def _extract_preferences(user_id: str, raw_text: str) -> dict:
    from agents import preference_extraction_agent
    db_session.init_db(settings.database_url)
    return await preference_extraction_agent.run({
        "user_id": user_id,
        "text": raw_text,
    })


async def _run_pipeline(user_id: str, user_email: str):
    try:
        from graph.pipeline import build_pipeline
    except ImportError:
        raise RuntimeError("Pipeline not available — could not import graph/pipeline.py.")

    db_session.init_db(settings.database_url)
    pref = await _get_preference(uuid.UUID(user_id))
    if pref:
        interests_str = ", ".join(pref.interests)
        excluded_str = ", ".join(pref.excluded_topics)
        raw_text = f"I'm interested in {interests_str}."
        if excluded_str:
            raw_text += f" Exclude {excluded_str}."
        raw_text += f" Send me {pref.article_count} articles."
    else:
        raw_text = "I'm interested in AI, FinTech, and Tech news. Send me 5 articles."

    pipeline = build_pipeline()
    initial_state = {
        "user_id": user_id,
        "user_email": user_email,
        "raw_preferences": {"text": raw_text},
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
    }
    final_state = await pipeline.ainvoke(initial_state)
    return final_state.get("digest", ""), final_state.get("pipeline_status", "")

# ── Page: Login ───────────────────────────────────────────────────────────────

def page_login():
    st.markdown("""
        <div style="text-align:center; padding: 60px 0 20px 0;">
            <div style="font-size:48px; margin-bottom:12px;">⚡</div>
            <h1 style="font-size:42px; font-weight:700; background: linear-gradient(135deg, #6c63ff, #4facfe);
                -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0;">
                InsightStream
            </h1>
            <p style="color:#4a5568; font-size:16px; margin-top:8px;">
                Your AI-powered daily news digest
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("""
            <div style="background:#13131f; border:1px solid #1e1e3a; border-radius:16px; padding:32px;">
        """, unsafe_allow_html=True)

        email = st.text_input("Email", placeholder="Enter your email address", label_visibility="collapsed").strip().lower()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Login", use_container_width=True):
                if not email:
                    st.warning("Please enter your email.")
                else:
                    user = run(_get_user_by_email(email))
                    if user is None:
                        st.error("No account found. Register first.")
                    else:
                        _set_session(user)
                        st.rerun()
        with c2:
            if st.button("Register", use_container_width=True):
                if not email:
                    st.warning("Please enter your email.")
                else:
                    existing = run(_get_user_by_email(email))
                    user = existing if existing else run(_create_user(email))
                    _set_session(user)
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
        <p style="text-align:center; color:#2d2d5e; font-size:13px; margin-top:40px;">
            Powered by Claude · Llama · LangGraph
        </p>
    """, unsafe_allow_html=True)


def _set_session(user: User):
    st.session_state.user_id = str(user.id)
    st.session_state.user_email = user.email
    st.session_state.is_subscribed = user.is_subscribed
    st.session_state.page = "dashboard"

# ── Page: Dashboard ───────────────────────────────────────────────────────────

def page_dashboard():
    uid = uuid.UUID(st.session_state.user_id)
    pref = run(_get_preference(uid))
    is_subscribed = st.session_state.get("is_subscribed", False)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
            <div>
                <h1 style="font-size:28px; font-weight:700; margin:0;
                    background:linear-gradient(135deg,#6c63ff,#4facfe);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                    InsightStream
                </h1>
                <p style="color:#4a5568; font-size:13px; margin:2px 0 0 0;">
                    {st.session_state.user_email}
                </p>
            </div>
            <div style="background:{'rgba(72,199,142,0.15)' if is_subscribed else 'rgba(255,82,82,0.1)'};
                border:1px solid {'rgba(72,199,142,0.4)' if is_subscribed else 'rgba(255,82,82,0.3)'};
                border-radius:20px; padding:4px 14px; font-size:12px; font-weight:600;
                color:{'#48c78e' if is_subscribed else '#ff5252'};">
                {'● SUBSCRIBED' if is_subscribed else '○ NOT SUBSCRIBED'}
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── Two-column layout ─────────────────────────────────────────────────────
    left, right = st.columns([3, 2], gap="large")

    with left:
        # ── Preferences card ──────────────────────────────────────────────────
        st.markdown("""
            <p style="color:#6c63ff; font-size:11px; font-weight:600;
                letter-spacing:1.5px; text-transform:uppercase; margin-bottom:12px;">
                Preferences
            </p>
        """, unsafe_allow_html=True)

        raw_text = st.text_area(
            "Describe what news you want",
            height=110,
            placeholder=(
                "e.g. I'm a software engineer interested in AI startups, large language models "
                "and FinTech. I follow generative AI research and venture capital deals. "
                "Please avoid crypto and NFT news."
            ),
        )

        if st.button("Extract with AI", use_container_width=True):
            if not raw_text.strip():
                st.warning("Describe your interests first.")
            else:
                with st.spinner("Analyzing with Claude..."):
                    try:
                        extracted = run(_extract_preferences(st.session_state.user_id, raw_text))
                        st.session_state.extracted_interests = ", ".join(extracted.get("interests", []))
                        st.session_state.extracted_excluded = ", ".join(extracted.get("excluded_topics", []))
                        st.session_state.extracted_count = extracted.get("article_count", 5)
                        st.success("Done! Review the fields below.")
                    except Exception as e:
                        st.error(f"Extraction failed: {e}")

        existing_interests = st.session_state.pop("extracted_interests", None) \
            or (", ".join(pref.interests) if pref else "")
        existing_excluded = st.session_state.pop("extracted_excluded", None) \
            or (", ".join(pref.excluded_topics) if pref else "")
        existing_count = st.session_state.pop("extracted_count", None) \
            or (pref.article_count if pref else 5)

        interests_raw = st.text_input("Interests", value=existing_interests,
                                       placeholder="AI, FinTech, machine learning...")
        excluded_raw = st.text_input("Exclude topics", value=existing_excluded,
                                      placeholder="crypto, NFT, celebrity news...")
        article_count = st.slider("Articles per digest", min_value=1, max_value=15,
                                   value=int(existing_count))

        if st.button("Save Preferences", use_container_width=True, type="primary"):
            interests = [t.strip() for t in interests_raw.split(",") if t.strip()]
            excluded = [t.strip() for t in excluded_raw.split(",") if t.strip()]
            run(_upsert_preference(uid, interests, excluded, article_count))
            st.success("Preferences saved!")

    with right:
        # ── Subscription card ─────────────────────────────────────────────────
        st.markdown("""
            <p style="color:#6c63ff; font-size:11px; font-weight:600;
                letter-spacing:1.5px; text-transform:uppercase; margin-bottom:12px;">
                Daily Digest
            </p>
        """, unsafe_allow_html=True)

        if is_subscribed:
            st.markdown("""
                <div style="background:rgba(72,199,142,0.08); border:1px solid rgba(72,199,142,0.25);
                    border-radius:14px; padding:20px; margin-bottom:16px; text-align:center;">
                    <div style="font-size:28px; margin-bottom:8px;">📬</div>
                    <p style="color:#48c78e; font-weight:600; margin:0; font-size:14px;">
                        You're subscribed
                    </p>
                    <p style="color:#4a5568; font-size:12px; margin:6px 0 0 0;">
                        Digest delivered every day at 9:00 AM
                    </p>
                </div>
            """, unsafe_allow_html=True)

            if st.button("Unsubscribe", use_container_width=True):
                run(_toggle_subscription(uid, False))
                st.session_state.is_subscribed = False
                st.rerun()
        else:
            st.markdown("""
                <div style="background:rgba(108,99,255,0.08); border:1px solid rgba(108,99,255,0.25);
                    border-radius:14px; padding:20px; margin-bottom:16px; text-align:center;">
                    <div style="font-size:28px; margin-bottom:8px;">📭</div>
                    <p style="color:#a0aec0; font-weight:600; margin:0; font-size:14px;">
                        Not subscribed
                    </p>
                    <p style="color:#4a5568; font-size:12px; margin:6px 0 0 0;">
                        Subscribe to get news every day at 9:00 AM
                    </p>
                </div>
            """, unsafe_allow_html=True)

            if st.button("Subscribe to Daily Digest", use_container_width=True, type="primary"):
                run(_toggle_subscription(uid, True))
                st.session_state.is_subscribed = True
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Get News Now card ─────────────────────────────────────────────────
        st.markdown("""
            <p style="color:#6c63ff; font-size:11px; font-weight:600;
                letter-spacing:1.5px; text-transform:uppercase; margin-bottom:12px;">
                On-Demand
            </p>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style="background:#13131f; border:1px solid #1e1e3a;
                border-radius:14px; padding:20px; text-align:center; margin-bottom:16px;">
                <div style="font-size:28px; margin-bottom:8px;">⚡</div>
                <p style="color:#e2e8f0; font-weight:600; margin:0; font-size:14px;">
                    Get News Right Now
                </p>
                <p style="color:#4a5568; font-size:12px; margin:6px 0 0 0;">
                    Run the pipeline instantly and receive your digest
                </p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("Get News Now", use_container_width=True):
            with st.spinner("Fetching your personalized digest..."):
                try:
                    digest_html, status = run(_run_pipeline(
                        st.session_state.user_id,
                        st.session_state.user_email,
                    ))
                    if status == "no_new_articles":
                        st.warning("No new articles found today. Try again later.")
                    elif status == "no_summaries":
                        st.warning("Summaries failed verification. Try again later.")
                    elif not digest_html:
                        st.warning("No digest produced. Check your preferences.")
                    else:
                        st.session_state.last_digest = digest_html
                        st.success("Digest sent to your email!")
                except RuntimeError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Pipeline error: {e}")

    # ── Digest Preview ────────────────────────────────────────────────────────
    if st.session_state.get("last_digest"):
        st.divider()
        st.markdown("""
            <p style="color:#6c63ff; font-size:11px; font-weight:600;
                letter-spacing:1.5px; text-transform:uppercase; margin-bottom:12px;">
                Latest Digest Preview
            </p>
        """, unsafe_allow_html=True)
        st.components.v1.html(st.session_state.last_digest, height=700, scrolling=True)

    # ── History ───────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("""
        <p style="color:#6c63ff; font-size:11px; font-weight:600;
            letter-spacing:1.5px; text-transform:uppercase; margin-bottom:12px;">
            Previously Sent Articles
        </p>
    """, unsafe_allow_html=True)

    history = run(_get_history(uid))
    if not history:
        st.markdown("<p style='color:#2d2d5e; font-size:14px;'>No articles sent yet.</p>",
                    unsafe_allow_html=True)
    else:
        for item in history:
            cat = item["category"] or "General"
            st.markdown(f"""
                <div style="display:flex; align-items:flex-start; justify-content:space-between;
                    padding:14px 0; border-bottom:1px solid #1a1a2e;">
                    <div style="flex:1; min-width:0; padding-right:16px;">
                        <a href="{item['url']}" target="_blank"
                            style="color:#e2e8f0; font-size:14px; font-weight:500;
                            text-decoration:none; line-height:1.4;">
                            {item['title']}
                        </a>
                        <p style="color:#4a5568; font-size:12px; margin:4px 0 0 0;">
                            {item['source']} · {item['sent_at']}
                        </p>
                    </div>
                    <span style="background:rgba(108,99,255,0.15); color:#6c63ff;
                        padding:3px 10px; border-radius:20px; font-size:11px;
                        font-weight:600; white-space:nowrap; flex-shrink:0;">
                        {cat}
                    </span>
                </div>
            """, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

def sidebar():
    with st.sidebar:
        st.markdown("""
            <div style="padding:16px 0 8px 0;">
                <span style="font-size:20px; font-weight:700;
                    background:linear-gradient(135deg,#6c63ff,#4facfe);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                    ⚡ InsightStream
                </span>
            </div>
        """, unsafe_allow_html=True)

        if "user_email" in st.session_state:
            st.markdown(f"""
                <div style="padding:12px; background:#13131f; border:1px solid #1e1e3a;
                    border-radius:10px; margin:12px 0;">
                    <p style="margin:0; font-size:13px; font-weight:500; color:#e2e8f0 !important;">
                        {st.session_state.user_email}
                    </p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("---")
            if st.button("Dashboard", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                for key in ["user_id", "user_email", "is_subscribed", "page", "last_digest"]:
                    st.session_state.pop(key, None)
                st.rerun()

        st.markdown("""
            <div style="position:fixed; bottom:20px; font-size:11px; color:#2d2d5e;">
                Powered by Claude · Llama · LangGraph
            </div>
        """, unsafe_allow_html=True)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="InsightStream",
        page_icon="⚡",
        layout="wide",
    )
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    sidebar()

    if "user_id" not in st.session_state:
        page_login()
    else:
        page_dashboard()


if __name__ == "__main__":
    main()
