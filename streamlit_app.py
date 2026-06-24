"""All Cars Direct — car lease/buy broker marketplace (Streamlit)."""
from __future__ import annotations

import streamlit as st

from lib import auth, db, styles

from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"
# Prefer the 32px PNG for Streamlit's set_page_config (it accepts a single
# image and renders best at 32px). The link tags below provide the rest.
_FAVICON = _ASSETS / "favicon-32.png"

st.set_page_config(
    page_title="All Cars Direct — Smarter Car Deals",
    page_icon=str(_FAVICON) if _FAVICON.exists() else ":material/directions_car:",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Streamlit's page_icon only sets a single favicon link. Inject the rest as
# inline data URIs so desktop browsers, retina screens, and iOS home-screen
# pins all get an appropriate icon — no static-file-serving config required.
def _favicon_links() -> str:
    import base64
    parts = []
    for name, rel, mime, size in (
        ("favicon.svg",     "icon",            "image/svg+xml", None),
        ("favicon-16.png",  "icon",            "image/png",     "16x16"),
        ("favicon-32.png",  "icon",            "image/png",     "32x32"),
        ("favicon-48.png",  "icon",            "image/png",     "48x48"),
        ("favicon-96.png",  "icon",            "image/png",     "96x96"),
        ("favicon-180.png", "apple-touch-icon", "image/png",    "180x180"),
    ):
        p = _ASSETS / name
        if not p.exists():
            continue
        b64 = base64.b64encode(p.read_bytes()).decode()
        sz = f" sizes='{size}'" if size else ""
        parts.append(f"<link rel='{rel}' type='{mime}'{sz} href='data:{mime};base64,{b64}'>")
    return "\n".join(parts)


st.markdown(_favicon_links(), unsafe_allow_html=True)

# Ensure DB schema exists. Inventory comes from the admin Sources page
# (web crawler) or the CSV bulk upload — no auto-seed.
db.init_db()
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
dealers = st.Page("views/dealers.py", title="For Dealers",
                  icon=":material/storefront:", url_path="dealers")
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
pg = st.navigation([home, browse, how, about, dealers,
                    dashboard, requests_pg, manage, upload, sources],
                   position="hidden")

styles.top_nav(active_path=pg.url_path)

# Admin pages get their own back-office sub-nav (never shown to customers).
ADMIN_PATHS = {"admin", "admin-requests", "admin-listings", "admin-upload", "admin-sources"}
if pg.url_path in ADMIN_PATHS and auth.is_authed():
    styles.admin_subnav(active_path=pg.url_path)

pg.run()
