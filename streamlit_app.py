"""All Cars Direct — car lease/buy broker marketplace (Streamlit)."""
from __future__ import annotations

import streamlit as st

from lib import auth, db, seed, styles

from pathlib import Path

_FAVICON = Path(__file__).parent / "assets" / "favicon.png"

st.set_page_config(
    page_title="All Cars Direct — Smarter Car Deals",
    page_icon=str(_FAVICON) if _FAVICON.exists() else ":material/directions_car:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Ensure DB schema exists. Seed sample inventory on first run so the storefront
# always has something to show — seed is a no-op once any listings exist, so
# the crawler / CSV-uploaded data is never overwritten.
db.init_db()
seed.seed_if_empty()
styles.inject()

# Log out via the header link (/?logout=1).
if "logout" in st.query_params:
    st.session_state["ll_admin_ok"] = False
    del st.query_params["logout"]

home = st.Page("views/home.py", title="All Cars Direct",
               icon=":material/home:", default=True)
browse = st.Page("views/browse.py", title="Browse Deals",
                 icon=":material/directions_car:", url_path="deals")
how = st.Page("views/how_it_works.py", title="How It Works",
              icon=":material/route:", url_path="how-it-works")
about = st.Page("views/about.py", title="About",
                icon=":material/info:", url_path="about")
dashboard = st.Page("views/dashboard.py", title="Dashboard",
                    icon=":material/dashboard:", url_path="admin")
requests_pg = st.Page("views/requests.py", title="Requests",
                      icon=":material/inbox:", url_path="admin-requests")
manage = st.Page("views/manage.py", title="Manage Listings",
                 icon=":material/build:", url_path="admin-listings")
upload = st.Page("views/upload.py", title="Bulk CSV Upload",
                 icon=":material/upload:", url_path="admin-upload")
sources = st.Page("views/sources.py", title="Sources",
                  icon=":material/cloud_download:", url_path="admin-sources")

# Navigation lives in our custom top header; hide Streamlit's built-in menu.
# Admin pages are reachable only by URL (sign in at /admin) and, once
# authenticated, via the admin links that appear in the header.
pg = st.navigation([home, browse, how, about, dashboard, requests_pg, manage, upload, sources],
                   position="hidden")

styles.top_nav(active_path=pg.url_path)

# Admin pages get their own back-office sub-nav (never shown to customers).
ADMIN_PATHS = {"admin", "admin-requests", "admin-listings", "admin-upload", "admin-sources"}
if pg.url_path in ADMIN_PATHS and auth.is_authed():
    styles.admin_subnav(active_path=pg.url_path)

pg.run()
