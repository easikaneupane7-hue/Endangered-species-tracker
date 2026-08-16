import json
import smtplib
from email.message import EmailMessage
from pathlib import Path

import streamlit as st

from auth_utils import ensure_authenticated
from app_theme import apply_theme

FEEDBACK_PATH = Path(__file__).resolve().parent.parent / "feedback.json"
NOTIFY_EMAIL = "easikaneupane3@gmail.com"


def _get_email_credentials():
    try:
        email_section = st.secrets.get("email", {})
    except Exception:
        email_section = {}

    sender = email_section.get("address") or __import__("os").getenv("EMAIL_ADDRESS")
    app_password = email_section.get("password") or __import__("os").getenv("EMAIL_PASSWORD")
    return sender, app_password


def _send_feedback_email(name: str, email: str, message: str) -> tuple[bool, str]:
    sender, app_password = _get_email_credentials()
    if not sender or not app_password:
        return False, "Email not configured (missing EMAIL_ADDRESS/EMAIL_PASSWORD)."

    msg = EmailMessage()
    msg["Subject"] = f"New feedback from {name}"
    msg["From"] = sender
    msg["To"] = NOTIFY_EMAIL
    if email:
        msg["Reply-To"] = email
    msg.set_content(
        f"New feedback submitted on Endangered Species Tracker.\n\n"
        f"Name: {name}\n"
        f"Email: {email or 'not provided'}\n\n"
        f"Message:\n{message}"
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.send_message(msg)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def render():
    if not ensure_authenticated():
        return

    apply_theme("feedback")

    st.title("💬 Feedback")
    st.caption("Share your thoughts or suggestions.")

    def load_feedback():
        if FEEDBACK_PATH.exists():
            try:
                with FEEDBACK_PATH.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                return []
        return []

    def save_feedback(items):
        with FEEDBACK_PATH.open("w", encoding="utf-8") as fh:
            json.dump(items, fh, indent=2)

    st.markdown('<div class="info-card-dark">', unsafe_allow_html=True)
    with st.form("feedback_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        message = st.text_area("Your feedback")
        submitted = st.form_submit_button("Submit feedback")

        if submitted:
            if not name or not message:
                st.error("Please fill in your name and feedback message.")
            else:
                items = load_feedback()
                items.append({"name": name, "email": email, "message": message})
                save_feedback(items)
                st.success("Thank you for your feedback.")

                sent, error = _send_feedback_email(name, email, message)
                if not sent:
                    st.warning(f"Feedback saved, but the notification email did not send: {error}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    st.subheader("Recent feedback")
    feedback_items = load_feedback()
    if feedback_items:
        recent = feedback_items[-5:][::-1]  # most recent first
        for item in recent:
            st.markdown('<div class="info-card-dark">', unsafe_allow_html=True)
            st.markdown(f"**{item.get('name', 'Anonymous')}**")
            st.write(item.get("message", ""))
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No feedback submitted yet.")