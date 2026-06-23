"""Lightweight admin password gate for the back-office pages."""
from __future__ import annotations

import streamlit as st

# Admin login gate. When True every back-office page is accessible without a
# password — only flip this on for local development. Production / shared
# previews keep this False; the password lives in .streamlit/secrets.toml
# (key: ``admin_password``). Default password is "admin" if no secret is set.
DISABLE_AUTH = False

# Feature flag: when False, the web crawler is shown in the admin but Sync
# actions are blocked (with an explanatory banner). Flip to True to re-enable
# live crawling. Kept here so it lives next to the other "ops switches".
CRAWLER_ENABLED = False

_DEFAULT_PASSWORD = "admin"


def is_authed() -> bool:
    """True when the admin area should be accessible (gate off or signed in)."""
    return DISABLE_AUTH or bool(st.session_state.get("ll_admin_ok"))


def _expected_password() -> str:
    try:
        return st.secrets["admin_password"]  # type: ignore[index]
    except Exception:
        return _DEFAULT_PASSWORD


def require_admin() -> bool:
    """Render a login gate. Returns True only when authenticated.

    The log-out control and admin navigation live in the app shell
    (streamlit_app.py), which renders them once the session is authenticated.
    """
    if DISABLE_AUTH or st.session_state.get("ll_admin_ok"):
        return True

    st.markdown("### :material/lock: Admin sign-in")
    st.caption("Enter the admin password to manage inventory.")
    with st.form("admin_login", clear_on_submit=False):
        pw = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", icon=":material/login:")
    if submitted:
        if pw == _expected_password():
            st.session_state["ll_admin_ok"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False
