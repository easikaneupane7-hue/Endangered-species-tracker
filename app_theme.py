"""
app_theme.py

Visual theming engine for the app:
  - A one-time animated splash/opening screen per session.
  - Distinct animated backgrounds per page (space / purple glitter / etc).
  - Reusable CSS classes for presenting data as styled "info cards"
    instead of raw st.dataframe rows-and-columns.

Usage in app.py (near the very top, right after st.set_page_config):

    from app_theme import show_splash, apply_theme
    show_splash()
    apply_theme("home")

And in each pages/*.py render():

    from app_theme import apply_theme
    apply_theme("dashboard")   # or "search", "space", "purple", etc.
"""

import time
import streamlit as st

# ---------------------------------------------------------------------------
# Page -> theme mapping. Edit freely — any page name below can point to any
# theme key in THEMES.
# ---------------------------------------------------------------------------
PAGE_THEMES = {
    "home": "aurora",
    "dashboard": "space",
    "search": "purple_glitter",
    "overview": "forest",
    "feedback": "sunset",
    "settings": "midnight",
    "policies": "emerald_gold",
}

THEMES = {
    "space": """
        background: radial-gradient(ellipse at bottom, #0d1224 0%, #000000 100%);
        background-image:
            radial-gradient(2px 2px at 20px 30px, #eee, transparent),
            radial-gradient(2px 2px at 60px 120px, #fff, transparent),
            radial-gradient(1.5px 1.5px at 100px 60px, #ddd, transparent),
            radial-gradient(1.5px 1.5px at 160px 20px, #fff, transparent),
            radial-gradient(2px 2px at 200px 140px, #eee, transparent),
            radial-gradient(1.5px 1.5px at 240px 90px, #fff, transparent),
            radial-gradient(ellipse at bottom, #0d1224 0%, #000000 100%);
        background-repeat: repeat;
        background-size: 260px 200px, 260px 200px, 260px 200px, 260px 200px,
                          260px 200px, 260px 200px, cover;
        animation: twinkle 6s linear infinite;
    """,
    "purple_glitter": """
        background: linear-gradient(135deg, #2b0b4f 0%, #6a1b9a 45%, #8e2de2 100%);
        background-image:
            radial-gradient(1.5px 1.5px at 10% 20%, rgba(255,255,255,0.9), transparent),
            radial-gradient(1.5px 1.5px at 80% 10%, rgba(255,255,255,0.8), transparent),
            radial-gradient(1.5px 1.5px at 60% 70%, rgba(255,255,255,0.9), transparent),
            radial-gradient(1.5px 1.5px at 30% 80%, rgba(255,255,255,0.7), transparent),
            radial-gradient(1.5px 1.5px at 90% 50%, rgba(255,255,255,0.8), transparent),
            linear-gradient(135deg, #2b0b4f 0%, #6a1b9a 45%, #8e2de2 100%);
        background-size: 220px 220px, 220px 220px, 220px 220px, 220px 220px, 220px 220px, cover;
        animation: glitter 3s linear infinite;
    """,
    "forest": """
        background: linear-gradient(160deg, #0b3d0b 0%, #1f5f2e 50%, #2e7d32 100%);
    """,
    "sunset": """
        background: linear-gradient(160deg, #ff6a00 0%, #ee0979 60%, #6a0dad 100%);
    """,
    "midnight": """
        background: linear-gradient(160deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    """,
    "aurora": """
        background: linear-gradient(160deg, #003973 0%, #0072ff 40%, #38ef7d 100%);
    """,
    "parchment": """
        background: linear-gradient(160deg, #f5e6c8 0%, #e8d5a8 100%);
    """,
    "emerald_gold": """
        background: linear-gradient(160deg, #08251b 0%, #114d34 45%, #1c6e4a 100%);
        background-image:
            radial-gradient(1.5px 1.5px at 15% 25%, rgba(255,215,120,0.55), transparent),
            radial-gradient(1.5px 1.5px at 75% 15%, rgba(255,215,120,0.4), transparent),
            radial-gradient(1.5px 1.5px at 55% 65%, rgba(255,215,120,0.5), transparent),
            radial-gradient(1.5px 1.5px at 25% 80%, rgba(255,215,120,0.4), transparent),
            radial-gradient(1.5px 1.5px at 90% 55%, rgba(255,215,120,0.45), transparent),
            linear-gradient(160deg, #08251b 0%, #114d34 45%, #1c6e4a 100%);
        background-size: 240px 240px, 240px 240px, 240px 240px, 240px 240px, 240px 240px, cover;
        animation: glitter 5s linear infinite;
    """,
}

_KEYFRAMES = """
@keyframes twinkle {
    0%   { background-position: 0 0, 0 0, 0 0, 0 0, 0 0, 0 0, 0 0; }
    50%  { filter: brightness(1.3); }
    100% { background-position: 0 0, 0 0, 0 0, 0 0, 0 0, 0 0, 0 0; }
}
@keyframes glitter {
    0%   { filter: brightness(1) saturate(1); }
    50%  { filter: brightness(1.25) saturate(1.3); }
    100% { filter: brightness(1) saturate(1); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 12px rgba(255,255,255,0.25); }
    50%      { box-shadow: 0 0 28px rgba(255,255,255,0.55); }
}
"""

_CARD_CSS = """
.info-card {
    background: rgba(255,255,255,0.92);
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.1rem;
    box-shadow: 0 6px 20px rgba(0,0,0,0.18);
    animation: fadeInUp 0.5s ease both;
}
.info-card-dark {
    background: rgba(20,20,30,0.72);
    color: #f2f2f2;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1.1rem;
    box-shadow: 0 6px 20px rgba(0,0,0,0.35);
    backdrop-filter: blur(6px);
    animation: fadeInUp 0.5s ease both;
}
.info-card-title {
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
    opacity: 0.85;
}
.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.78rem;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    color: white;
}
.section-divider {
    border: none;
    height: 2px;
    margin: 1.4rem 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.6), transparent);
}
"""


def _inject(css: str):
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def apply_theme(page_key: str | None = None):
    """Apply the background theme + shared card CSS for a given page key.
    If page_key is None, looks it up from PAGE_THEMES using the current
    st.session_state page_nav value, defaulting to 'aurora'.
    """
    if page_key is None:
        page_key = PAGE_THEMES.get(st.session_state.get("page_nav", "Home").lower(), "aurora")
    theme_css = THEMES.get(page_key, THEMES.get(PAGE_THEMES.get(page_key, "aurora"), THEMES["aurora"]))
    # Allow passing either a theme key (e.g. "space") or a page name (e.g. "dashboard")
    if page_key in PAGE_THEMES and page_key not in THEMES:
        theme_css = THEMES[PAGE_THEMES[page_key]]

    _inject(f"""
        {_KEYFRAMES}
        .stApp {{
            {theme_css}
        }}
        section.main > div.block-container {{
            animation: fadeInUp 0.6s ease both;
        }}
        {_CARD_CSS}
    """)


def show_splash(app_name: str = "Endangered Species Tracker", seconds: float = 1.6):
    """Show a one-time animated opening screen for this browser session."""
    if st.session_state.get("_splash_shown"):
        return
    placeholder = st.empty()
    with placeholder.container():
        _inject(_KEYFRAMES)
        st.markdown(
            f"""
            <div style="
                height: 70vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background: radial-gradient(ellipse at center, #1b2a4a 0%, #05070f 100%);
                border-radius: 20px;
                animation: fadeInUp 0.5s ease both;
            ">
                <div style="
                    width: 64px; height: 64px;
                    border: 5px solid rgba(255,255,255,0.2);
                    border-top-color: #38ef7d;
                    border-radius: 50%;
                    animation: spin 0.9s linear infinite, pulseGlow 1.8s ease-in-out infinite;
                    margin-bottom: 1.5rem;
                "></div>
                <div style="color: white; font-size: 1.4rem; font-weight: 700; letter-spacing: 0.03em;">
                    🌍 {app_name}
                </div>
                <div style="color: #9fb3d8; font-size: 0.95rem; margin-top: 0.4rem;">
                    Loading conservation data...
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(seconds)
    placeholder.empty()
    st.session_state["_splash_shown"] = True


def status_color(status: str) -> str:
    """Rough IUCN-style color coding for a status string."""
    s = (status or "").strip().casefold()
    mapping = {
        "extinct": "#000000",
        "extinct in the wild": "#4a0d0d",
        "critically endangered": "#d32f2f",
        "endangered": "#f57c00",
        "vulnerable": "#fbc02d",
        "near threatened": "#afb42b",
        "least concern": "#388e3c",
        "data deficient": "#757575",
    }
    for key, color in mapping.items():
        if key in s:
            return color
    return "#607d8b"


# ---------------------------------------------------------------------------
# Small decorative touches (cartoonish emoji dividers) + a reusable inline
# loading animation for use around data-fetching calls.
# ---------------------------------------------------------------------------
import random
from contextlib import contextmanager

_DECOR_EMOJI = ["🐾", "🌿", "🦋", "🍃", "🐢", "🦉", "🐝", "🌸", "🦜", "🐬"]


def decor_divider(count: int = 5):
    """Render a small row of playful emoji as a lightweight section break."""
    picks = random.sample(_DECOR_EMOJI, k=min(count, len(_DECOR_EMOJI)))
    st.markdown(
        f"""
        <div style="text-align:center; font-size:1.3rem; opacity:0.85; margin: 0.6rem 0 1.1rem 0; letter-spacing:0.5rem;">
            {' '.join(picks)}
        </div>
        """,
        unsafe_allow_html=True,
    )


@contextmanager
def loading_animation(message: str = "Loading..."):
    """Inline spinner animation to wrap around slower calls (data fetches,
    API calls, etc). Usage:

        with loading_animation("Fetching species data..."):
            species = load_species_data()
    """
    placeholder = st.empty()
    placeholder.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:0.7rem; padding:0.6rem 0;">
            <div style="
                width: 22px; height: 22px;
                border: 3px solid rgba(255,255,255,0.25);
                border-top-color: #38ef7d;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            "></div>
            <span style="opacity:0.85; font-weight:600;">{message}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        placeholder.empty()