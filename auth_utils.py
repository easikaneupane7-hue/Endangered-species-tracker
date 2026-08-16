import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

import streamlit as st

USER_STORE_PATH = Path(__file__).resolve().parent / "users.json"

PBKDF2_ITERATIONS = 260_000
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 30


def get_login_credentials():
    try:
        app_section = st.secrets.get("app", {})
    except Exception:
        app_section = {}

    username = app_section.get("username") or os.getenv("APP_USERNAME")
    password = app_section.get("password") or os.getenv("APP_PASSWORD")
    return username, password


def _hash_with_salt(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return digest.hex()


def hash_password(password: str) -> str:
    """Create a new salted hash in the form 'salt_hex$hash_hex'."""
    salt = secrets.token_bytes(16)
    return f"{salt.hex()}${_hash_with_salt(password, salt)}"


def _legacy_hash(password: str) -> str:
    """Old unsalted SHA-256 format, kept only to verify pre-existing accounts."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _verify_password(password: str, stored: str) -> tuple[bool, bool]:
    """Return (is_valid, needs_upgrade_to_salted_hash)."""
    if "$" in stored:
        salt_hex, hash_hex = stored.split("$", 1)
        try:
            salt = bytes.fromhex(salt_hex)
        except ValueError:
            return False, False
        candidate = _hash_with_salt(password, salt)
        return hmac.compare_digest(candidate, hash_hex), False

    is_valid = hmac.compare_digest(_legacy_hash(password), stored)
    return is_valid, is_valid


def load_users() -> dict:
    if USER_STORE_PATH.exists():
        try:
            with USER_STORE_PATH.open("r", encoding="utf-8") as fh:
                users = json.load(fh)
                if isinstance(users, dict):
                    return users
        except Exception:
            pass

    default_user, default_pass = get_login_credentials()
    users = {}

    if default_user and default_pass:
        users[default_user] = hash_password(default_pass)
    else:
        default_user = "admin"
        default_pass = secrets.token_urlsafe(12)
        users[default_user] = hash_password(default_pass)
        st.warning(
            f"No APP_USERNAME/APP_PASSWORD configured. Created account "
            f"'{default_user}' with password: {default_pass}\n\n"
            "Save this now — it will not be shown again. Set APP_USERNAME and "
            "APP_PASSWORD (or st.secrets['app']) to control this instead."
        )

    save_users(users)
    return users


def save_users(users: dict) -> None:
    with USER_STORE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(users, fh, indent=2)


def authenticate(username: str, password: str) -> bool:
    users = load_users()
    stored_hash = users.get(username)
    if not stored_hash:
        return False

    is_valid, needs_upgrade = _verify_password(password, stored_hash)
    if is_valid and needs_upgrade:
        users[username] = hash_password(password)
        save_users(users)
    return is_valid


def _login_state_key(username: str) -> str:
    return f"_login_attempts::{username}"


def _lockout_remaining_seconds(username: str) -> float:
    state = st.session_state.get(_login_state_key(username))
    if not state:
        return 0
    attempts, locked_until = state
    if attempts < MAX_LOGIN_ATTEMPTS:
        return 0
    return max(0, locked_until - time.time())


def _register_attempt(username: str, success: bool) -> None:
    key = _login_state_key(username)
    if success:
        st.session_state.pop(key, None)
        return

    attempts, _ = st.session_state.get(key, (0, 0))
    attempts += 1
    locked_until = time.time() + LOCKOUT_SECONDS if attempts >= MAX_LOGIN_ATTEMPTS else 0
    st.session_state[key] = (attempts, locked_until)


def show_login():
    st.session_state.setdefault("authenticated", False)
    st.session_state.setdefault("current_user", None)

    if st.session_state.get("authenticated", False):
        return True

    st.title("🔐 Login / Sign up")
    st.caption("Access the protected endangered-species dashboard.")

    auth_mode = st.radio("Choose an option", ["Login", "Sign up"], horizontal=True)

    if auth_mode == "Login":
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")

            if submitted:
                remaining = _lockout_remaining_seconds(username)
                if remaining > 0:
                    st.error(f"Too many failed attempts. Try again in {int(remaining)}s.")
                elif authenticate(username, password):
                    _register_attempt(username, success=True)
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = username
                    st.session_state["auth_message"] = None
                    st.success("Signed in.")
                    st.rerun()
                else:
                    _register_attempt(username, success=False)
                    st.session_state["auth_message"] = "Invalid username or password."
                    st.error("Invalid username or password.")

    else:
        with st.form("signup_form"):
            new_user = st.text_input("Choose username", key="signup_username")
            new_password = st.text_input("Choose password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Create account")

            if submitted:
                if not new_user or not new_password or not confirm_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    users = load_users()
                    if new_user in users:
                        st.error("That username already exists.")
                    else:
                        users[new_user] = hash_password(new_password)
                        save_users(users)
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = new_user
                        st.session_state["auth_message"] = f"Account created for {new_user}."
                        st.success("Account created successfully.")
                        st.rerun()

    if st.session_state.get("auth_message"):
        st.info(st.session_state["auth_message"])

    return False


def ensure_authenticated():
    if st.session_state.get("authenticated", False):
        return True
    return show_login()