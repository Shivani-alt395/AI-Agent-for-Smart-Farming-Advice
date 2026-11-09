"""
Smart Farming AI Agent — Streamlit frontend.

Reuses the existing `app/` package (RAG + IBM Granite + weather + mandi + auth)
directly, so no FastAPI server is needed.  Place this file in the project root
(next to the `app/` folder) and run:

    streamlit run streamlit_app.py
"""
from __future__ import annotations

# ── 0. Environment bootstrap (must run BEFORE importing anything from `app`) ──
import os
import sys

# ChromaDB needs SQLite >= 3.35. Streamlit Cloud's system SQLite is older,
# so swap in pysqlite3-binary when available.
try:
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

import streamlit as st

st.set_page_config(
    page_title="Smart Farming AI Agent",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Copy Streamlit secrets -> environment variables so pydantic Settings picks them up.
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, (str, int, float, bool)):
            os.environ.setdefault(str(_k).upper(), str(_v))
except Exception:
    pass  # no secrets file — fall back to .env / defaults (demo mode)

import asyncio
import uuid
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd

from app.models.schemas import FarmingQuery, Language

# ── 1. Constants ──────────────────────────────────────────────────────────────
LANGUAGES: Dict[str, str] = {
    "en": "English", "hi": "Hindi (हिंदी)", "mr": "Marathi (मराठी)",
    "te": "Telugu (తెలుగు)", "ta": "Tamil (தமிழ்)", "kn": "Kannada (ಕನ್ನಡ)",
    "gu": "Gujarati (ગુજરાતી)", "pa": "Punjabi (ਪੰਜਾਬੀ)", "bn": "Bengali (বাংলা)",
    "or": "Odia (ଓଡ଼ିଆ)",
}

STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
]

QUICK_QUESTIONS = [
    ("🌾 Best Kharif crop?", "What crop should I grow this Kharif season?"),
    ("💰 Tomato mandi price?", "What is today's mandi rate for tomatoes?"),
    ("🐛 Wheat pest control?", "How to control pests in wheat crop organically?"),
    ("💧 Rice irrigation?", "When should I irrigate my rice crop?"),
    ("🌱 Improve soil health?", "How to improve soil health naturally?"),
    ("🏛️ Govt schemes?", "What government schemes are available for small farmers?"),
    ("📋 Wheat MSP?", "What is the MSP for wheat this year?"),
    ("🍅 Tomato leaf curl?", "My tomato leaves are curling, what disease is this?"),
]

CATEGORY_BADGE = {
    "weather": "🌤️ Weather", "crop": "🌾 Crop", "pest": "🐛 Pest",
    "soil": "🌱 Soil", "market": "💰 Market", "general": "💬 General",
}

# ── 2. Helpers ────────────────────────────────────────────────────────────────
def run_async(coro):
    """Run an async coroutine from Streamlit's sync context."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


@st.cache_resource(show_spinner="Loading knowledge base & AI model (first run takes a minute)…")
def load_backend():
    """Initialise RAG, seed the vector store if empty, and build the agent. Runs once per server."""
    from app.core.rag_pipeline import get_rag_pipeline
    from app.services.knowledge_base import load_knowledge_base
    from app.services.farming_agent import get_farming_agent

    rag = get_rag_pipeline()
    if not rag.is_ready:
        load_knowledge_base()
    agent = get_farming_agent()
    granite_live = getattr(agent._llm, "_model", None) is not None
    return agent, granite_live


@st.cache_data(ttl=3600, show_spinner=False)
def geocode(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search Indian locations via Nominatim (OpenStreetMap)."""
    if not query or len(query.strip()) < 3:
        return []
    try:
        r = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{query} India", "format": "json", "limit": limit, "countrycodes": "in"},
            headers={"User-Agent": "SmartFarmingAI-Streamlit/1.0"},
            timeout=8.0,
        )
        r.raise_for_status()
        return [
            {"label": x["display_name"], "lat": float(x["lat"]), "lon": float(x["lon"])}
            for x in r.json()
        ]
    except Exception:
        return []


@st.cache_data(ttl=900, show_spinner=False)
def fetch_weather(lat: float, lon: float, name: str):
    from app.services.weather_service import WeatherService
    return run_async(WeatherService().get_weather(lat, lon, name, 7))


@st.cache_data(ttl=900, show_spinner=False)
def fetch_prices(state: Optional[str], commodity: Optional[str], limit: int = 8):
    from app.services.market_service import MarketService
    return run_async(MarketService().get_prices(commodity=commodity, state=state, limit=limit))


def init_state():
    ss = st.session_state
    ss.setdefault("user", None)
    ss.setdefault("messages", [])
    ss.setdefault("session_id", str(uuid.uuid4()))
    ss.setdefault("loc_name", "")
    ss.setdefault("lat", None)
    ss.setdefault("lon", None)
    ss.setdefault("otp_sent_to", None)
    ss.setdefault("otp_verified", False)
    ss.setdefault("pending_question", None)
    ss.setdefault("auth_disabled", False)


# ── 3. Auth page ──────────────────────────────────────────────────────────────
def auth_page():
    st.markdown("<h1 style='text-align:center'>🌾 Smart Farming AI Agent</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:gray'>Powered by IBM Granite · RAG · Live weather & mandi prices</p>",
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        tab_login, tab_reg = st.tabs(["🔑 Login", "📝 Register"])

        # ---- Login
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                pwd = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True, type="primary"):
                    from app.services.user_store import login_user
                    res = login_user(email, pwd)
                    if res["success"]:
                        st.session_state.user = res["user"]
                        u = res["user"]
                        st.session_state.loc_name = f"{u.get('district','')}, {u.get('state','')}".strip(", ")
                        st.rerun()
                    else:
                        st.error(res["message"])

        # ---- Register (email OTP)
        with tab_reg:
            st.caption("Step 1 — your details  →  Step 2 — verify email")
            name = st.text_input("Full name", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            pwd = st.text_input("Password (min 6 chars)", type="password", key="reg_pwd")
            c1, c2 = st.columns(2)
            state = c1.selectbox("State", [""] + STATES, key="reg_state")
            district = c2.text_input("District", key="reg_district")

            if st.button("Send verification code →", use_container_width=True):
                if not all([name, email, pwd, state, district]) or "@" not in email:
                    st.error("Please fill in all fields with a valid email.")
                elif len(pwd) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    from app.services.email_service import generate_otp, send_otp_email
                    otp = generate_otp(email)
                    result = send_otp_email(email, name, otp)
                    st.session_state.otp_sent_to = email
                    if result.get("mode") in ("console", "console_fallback"):
                        st.warning(f"SMTP not configured — demo mode. Your code: **{otp}**")
                    else:
                        st.success(f"Code sent to {email}. Check your inbox.")

            if st.session_state.otp_sent_to:
                otp_in = st.text_input("Enter 6-digit code", max_chars=6, key="reg_otp")
                if st.button("Verify & Register", type="primary", use_container_width=True):
                    from app.services.email_service import verify_otp
                    from app.services.user_store import register_user
                    if st.session_state.otp_sent_to.lower() != email.lower():
                        st.error("Email changed after sending the code. Please request a new one.")
                    elif not verify_otp(email, otp_in):
                        st.error("Invalid or expired code.")
                    else:
                        res = register_user(name, email, pwd, state, district)
                        if res["success"]:
                            st.session_state.user = res["user"]
                            st.session_state.loc_name = f"{district}, {state}"
                            st.session_state.otp_sent_to = None
                            st.rerun()
                        else:
                            st.error(res["message"])

        st.divider()
        if st.button("Continue as guest →", use_container_width=True):
            st.session_state.user = {"name": "Guest", "email": "", "state": "", "district": ""}
            st.rerun()


# ── 4. Sidebar ────────────────────────────────────────────────────────────────
def sidebar(granite_live: bool):
    ss = st.session_state
    with st.sidebar:
        st.markdown(f"### 👨‍🌾 {ss.user.get('name', 'Farmer')}")
        if ss.user.get("email"):
            st.caption(ss.user["email"])
        if st.button("Logout", use_container_width=True):
            for k in ("user", "messages", "otp_sent_to"):
                ss.pop(k, None)
            st.rerun()

        st.caption("🟢 IBM Granite connected" if granite_live
                   else "🟡 Demo mode — add IBM_API_KEY in secrets for Granite")

        st.divider()
        lang = st.selectbox(
            "🌐 Language / भाषा",
            options=list(LANGUAGES.keys()),
            format_func=lambda c: LANGUAGES[c],
            key="language",
        )

        st.divider()
        st.markdown("**📍 Farm location**")
        q = st.text_input("Search city or district", key="loc_query", placeholder="e.g. Nashik")
        if q:
            results = geocode(q)
            if results:
                pick = st.selectbox("Select match", range(len(results)),
                                    format_func=lambda i: results[i]["label"][:70])
                if st.button("Use this location", use_container_width=True):
                    ss.lat, ss.lon = results[pick]["lat"], results[pick]["lon"]
                    parts = [p.strip() for p in results[pick]["label"].split(",")]
                    ss.loc_name = ", ".join([parts[0], parts[-3] if len(parts) >= 3 else parts[-1]])
                    st.rerun()
            else:
                st.caption("No matches found.")
        elif ss.loc_name and ss.lat is None:
            # Registered users: geocode their profile location once
            res = geocode(ss.loc_name, 1)
            if res:
                ss.lat, ss.lon = res[0]["lat"], res[0]["lon"]

        if ss.loc_name:
            st.success(f"📍 {ss.loc_name}")

        # Weather widget
        if ss.lat is not None and ss.lon is not None:
            try:
                w = fetch_weather(ss.lat, ss.lon, ss.loc_name or "Your Farm")
                st.divider()
                st.markdown("**🌤️ Current weather**")
                c1, c2 = st.columns(2)
                c1.metric("Max", f"{w.temperature_max:.0f}°C")
                c2.metric("Min", f"{w.temperature_min:.0f}°C")
                c1.metric("Rain", f"{w.precipitation:.1f} mm")
                c2.metric("Wind", f"{w.wind_speed:.0f} km/h")
                st.caption(w.condition)
            except Exception:
                pass

        # Mandi widget
        state_guess = (ss.loc_name.split(",")[-1].strip() if ss.loc_name else None) or ss.user.get("state") or None
        try:
            prices = fetch_prices(state_guess, None, 5)
            if prices:
                st.divider()
                st.markdown(f"**💰 Mandi prices** {'— ' + state_guess if state_guess else ''}")
                st.dataframe(
                    pd.DataFrame([{"Crop": p.commodity, "Modal ₹/q": int(p.modal_price)} for p in prices]),
                    hide_index=True, use_container_width=True,
                )
        except Exception:
            pass

        st.divider()
        st.markdown("**💡 Quick questions**")
        for label, question in QUICK_QUESTIONS:
            if st.button(label, key=f"qq_{label}", use_container_width=True):
                ss.pending_question = question
                st.rerun()

        if st.button("🗑️ Clear chat", use_container_width=True):
            ss.messages = []
            ss.session_id = str(uuid.uuid4())
            st.rerun()


# ── 5. Rendering of an assistant message ──────────────────────────────────────
def render_assistant(msg: Dict[str, Any]):
    st.markdown(msg["content"])
    meta = msg.get("meta") or {}
    cat = meta.get("category")
    if cat:
        st.caption(f"{CATEGORY_BADGE.get(cat, cat)} · confidence {meta.get('confidence', 0):.0%}")

    market = meta.get("market_data")
    if market and market.get("prices"):
        df = pd.DataFrame(market["prices"])
        cols = [c for c in ["commodity", "market", "state", "min_price", "max_price", "modal_price"] if c in df]
        st.markdown("**💰 Mandi prices (₹ per quintal)**")
        st.dataframe(df[cols], hide_index=True, use_container_width=True)

    weather = meta.get("weather_data")
    if weather and weather.get("forecast_days"):
        with st.expander("🌤️ 7-day forecast"):
            fd = pd.DataFrame(weather["forecast_days"])
            st.dataframe(fd[["date", "condition", "temp_max", "temp_min", "precipitation", "wind_speed"]],
                         hide_index=True, use_container_width=True)

    sources = meta.get("sources")
    if sources:
        with st.expander(f"📚 Sources ({len(sources)})"):
            for s in sources:
                st.markdown(f"**{s['source']}** · relevance {s['relevance_score']:.0%}")
                st.caption(s["content"])


# ── 6. Main chat page ─────────────────────────────────────────────────────────
def chat_page():
    ss = st.session_state
    agent, granite_live = load_backend()
    sidebar(granite_live)

    st.title("🌾 Smart Farming AI Agent")
    st.caption("Ask about crops, weather, pests, soil, market prices & government schemes")

    if not ss.messages:
        ss.messages.append({
            "role": "assistant",
            "content": f"Namaste {ss.user.get('name', 'Farmer')}! 🙏 I'm your farming assistant. "
                       "Set your farm location in the sidebar for local weather and mandi advice, "
                       "then ask me anything.",
        })

    for m in ss.messages:
        with st.chat_message(m["role"], avatar="🌾" if m["role"] == "assistant" else "👨‍🌾"):
            if m["role"] == "assistant":
                render_assistant(m)
            else:
                st.markdown(m["content"])

    typed = st.chat_input("Ask a farming question…", max_chars=2000)
    question = typed or ss.pop("pending_question", None)
    if not question:
        return

    ss.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="👨‍🌾"):
        st.markdown(question)

    with st.chat_message("assistant", avatar="🌾"):
        with st.spinner("Thinking…"):
            try:
                query = FarmingQuery(
                    question=question,
                    language=Language(ss.get("language", "en")),
                    location=ss.loc_name or None,
                    latitude=ss.lat,
                    longitude=ss.lon,
                    session_id=ss.session_id,
                )
                resp = run_async(agent.process_query(query))
                msg = {
                    "role": "assistant",
                    "content": resp.answer,
                    "meta": {
                        "category": resp.category.value,
                        "confidence": resp.confidence,
                        "market_data": resp.market_data,
                        "weather_data": resp.weather_data,
                        "sources": [s.model_dump() for s in resp.sources],
                    },
                }
            except Exception as exc:
                msg = {"role": "assistant", "content": f"⚠️ Sorry, something went wrong: {exc}"}
        render_assistant(msg)
    ss.messages.append(msg)


# ── 7. Entry point ────────────────────────────────────────────────────────────
init_state()
if st.session_state.user is None:
    auth_page()
else:
    chat_page()
