"""
floating_chat.py

A floating, bring-your-own-API-key AI chatbot widget for Streamlit apps.

Usage (e.g. at the bottom of app.py, after your page routing):

    from floating_chat import render_floating_chat
    render_floating_chat()

The widget:
  - Shows a floating button in the bottom-right corner.
  - Clicking it opens a small chat panel (built with st.popover, so no
    custom JS/iframe hacks are needed).
  - On first use, asks the person to paste an API key from either
    Anthropic or OpenAI, with a link + instructions on how to create one.
  - The key is kept ONLY in st.session_state (never written to disk,
    never sent anywhere except directly to the chosen provider's API).
  - Once a key is saved, a normal chat interface (st.chat_message /
    st.chat_input) appears.
"""

import streamlit as st
import requests

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

ANTHROPIC_MODEL = "claude-sonnet-4-5"
OPENAI_MODEL = "gpt-4o-mini"

SESSION_KEYS = {
    "chat_provider": None,          # "anthropic" | "openai"
    "chat_api_key": None,           # raw key string, session-only
    "chat_messages": [],            # [{"role": "user"/"assistant", "content": str}]
}


def _init_state():
    for key, default in SESSION_KEYS.items():
        if key not in st.session_state:
            st.session_state[key] = default() if callable(default) else (
                [] if key == "chat_messages" else default
            )


def _inject_css():
    st.markdown(
        """
        <style>
        /* Push the popover trigger button into a floating bottom-right pill */
        div[data-testid="stPopover"] {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 9999;
        }
        div[data-testid="stPopover"] > div > button {
            border-radius: 50px !important;
            padding: 0.6rem 1.1rem !important;
            box-shadow: 0 4px 14px rgba(0,0,0,0.25) !important;
            font-weight: 600 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _key_setup_ui():
    st.markdown("**Connect your AI chatbot**")
    st.caption(
        "This chat runs on YOUR API key, not the app owner's. Nothing is "
        "stored on a server — the key lives only in this browser session."
    )

    provider = st.radio(
        "Provider",
        options=["Anthropic (Claude)", "OpenAI (ChatGPT)"],
        horizontal=True,
        key="chat_provider_choice",
    )

    if provider.startswith("Anthropic"):
        st.markdown(
            "1. Go to [console.anthropic.com](https://console.anthropic.com/settings/keys)\n"
            "2. Sign in (or create a free account)\n"
            "3. Click **Create Key**, give it any name\n"
            "4. Copy the key (starts with `sk-ant-...`) and paste it below"
        )
    else:
        st.markdown(
            "1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)\n"
            "2. Sign in (or create a free account)\n"
            "3. Click **Create new secret key**\n"
            "4. Copy the key (starts with `sk-...`) and paste it below"
        )

    key_input = st.text_input("Paste your API key", type="password", key="chat_key_input")

    if st.button("Connect", type="primary", use_container_width=True):
        if not key_input.strip():
            st.warning("Please paste a key first.")
        else:
            st.session_state.chat_api_key = key_input.strip()
            st.session_state.chat_provider = (
                "anthropic" if provider.startswith("Anthropic") else "openai"
            )
            st.rerun()


def _call_anthropic(api_key, messages):
    resp = requests.post(
        ANTHROPIC_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "messages": messages,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return "".join(
        block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"
    )


def _call_openai(api_key, messages):
    resp = requests.post(
        OPENAI_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "messages": messages,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _chat_ui():
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**Chat** · connected via {st.session_state.chat_provider}")
    with col2:
        if st.button("Disconnect", key="chat_disconnect"):
            st.session_state.chat_api_key = None
            st.session_state.chat_provider = None
            st.session_state.chat_messages = []
            st.rerun()

    chat_box = st.container(height=320)
    with chat_box:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    prompt = st.chat_input("Ask something...")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        try:
            with st.spinner("Thinking..."):
                if st.session_state.chat_provider == "anthropic":
                    reply = _call_anthropic(st.session_state.chat_api_key, st.session_state.chat_messages)
                else:
                    reply = _call_openai(st.session_state.chat_api_key, st.session_state.chat_messages)
        except requests.HTTPError as e:
            reply = f"⚠️ API error ({e.response.status_code}). Check that your key is valid and has quota."
        except Exception as e:
            reply = f"⚠️ Something went wrong: {e}"

        st.session_state.chat_messages.append({"role": "assistant", "content": reply})
        st.rerun()


def render_floating_chat():
    """Call this once per page to render the floating chat widget."""
    _init_state()
    _inject_css()

    with st.popover("💬 Chat"):
        if not st.session_state.chat_api_key:
            _key_setup_ui()
        else:
            _chat_ui()