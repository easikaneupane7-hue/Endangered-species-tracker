import streamlit as st

from auth_utils import ensure_authenticated


def render():
    if not ensure_authenticated():
        return

    st.title("⚙️ Settings")
    st.caption("Manage your account access and app preferences.")

    st.info(f"Signed in as: {st.session_state.get('current_user', 'user')}")

    if st.button("Logout"):
        st.session_state.clear()
        st.success("You have been logged out.")
        st.rerun()