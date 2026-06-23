"""Admin — manage web-crawler sources that pull inventory from external URLs."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from lib import auth, crawler, db, styles
from lib.icons import icon

styles.hero(
    "Inventory sources",
    "Add URLs the crawler should pull listings from. Run on demand.",
    icon_svg=icon("upload", 30, "#ffffff"),
)

if not auth.require_admin():
    st.stop()

if not auth.CRAWLER_ENABLED:
    st.warning(
        ":material/pause_circle: **Crawler is currently disabled.** Sources, "
        "their settings, and last-run history remain editable, but Sync actions "
        "won't run a live crawl. Flip `CRAWLER_ENABLED = True` in `lib/auth.py` "
        "to re-enable.",
        icon=":material/info:",
    )

sdf = db.fetch_crawl_sources_df()

# ----- Metric cards -----
total = len(sdf)
enabled = int(sdf["enabled"].sum()) if not sdf.empty else 0
errored = (
    int((sdf["last_status"].fillna("").str.startswith("Error")).sum())
    if not sdf.empty else 0
)
all_listings = db.fetch_df()
crawled_count = (
    int(all_listings["crawl_source_id"].notna().sum())
    if not all_listings.empty and "crawl_source_id" in all_listings.columns else 0
)
seeded_count = (
    int(all_listings["crawl_source_id"].isna().sum())
    if not all_listings.empty and "crawl_source_id" in all_listings.columns else 0
)
styles.metric_cards([
    ("layers", total, "Sources", "#0E2A47"),
    ("check-circle", enabled, "Enabled", "#16a34a"),
    ("inbox", crawled_count, "Crawled listings", "#2E8BFF"),
    ("bell", errored, "Errored last run", "#f59e0b"),
])

if seeded_count:
    cwarn1, cwarn2 = st.columns([4, 1], vertical_alignment="center")
    with cwarn1:
        st.warning(
            f"{seeded_count} sample listing(s) remain from the initial seed. "
            "Clear them so the storefront only shows real crawled inventory."
        )
    with cwarn2:
        if st.button("Clear sample inventory", type="secondary",
                     icon=":material/delete_sweep:", width="stretch"):
            removed = db.delete_seeded_listings()
            st.success(f"Removed {removed} sample listing(s).")
            st.rerun()

st.divider()

# ============================================================ Add a new source
styles.asection("Add a source", "upload")
with st.expander("How it works", expanded=False, icon=":material/info:"):
    st.markdown(
        "- The crawler **respects robots.txt** by default — disable on a per-source "
        "  basis only if you have permission to crawl that site.\n"
        "- Use the **Generic** parser first — it works on any page that publishes "
        "  schema.org `Vehicle`/`Car`/`Product` JSON-LD or Open Graph meta tags.\n"
        "- If a site has neither, switch to **Selectors** and provide CSS selectors "
        "  for title / price / image / etc. The config field accepts a JSON object "
        "  (see the placeholder for an example).\n"
        "- A selector list pattern like `\"list_links\": \"a.car-card\"` puts the "
        "  parser in **list-page mode** — it follows each detail link and parses it "
        "  with the same selectors."
    )

with st.form("add_source", clear_on_submit=True):
    c1, c2 = st.columns([2, 3])
    with c1:
        name = st.text_input("Name *", placeholder="e.g. Boston Lexus inventory")
    with c2:
        url = st.text_input("URL *", placeholder="https://example.com/inventory")
    c3, c4 = st.columns([2, 3])
    with c3:
        parser_kind = st.selectbox("Parser", db.CRAWLER_PARSER_KINDS, index=0)
    with c4:
        location = st.text_input(
            "Location (optional)",
            placeholder="e.g. Coral Springs, FL",
            help="Shown on every product card for this source. Overrides any "
                 "address the crawler parses from the page.",
        )
    config = st.text_area(
        "Config (optional JSON)",
        placeholder='{"title": "h1", "price": ".price", "image": "img.hero@src"}',
        height=80,
    )
    add_clicked = st.form_submit_button("Add source", type="primary",
                                        icon=":material/add:")
if add_clicked:
    if not name.strip() or not url.strip():
        st.error("Name and URL are required.")
    elif config.strip():
        try:
            json.loads(config)
        except json.JSONDecodeError as exc:
            st.error(f"Config isn't valid JSON: {exc}")
            st.stop()
    else:
        db.insert_crawl_source({
            "name": name.strip(), "url": url.strip(),
            "parser_kind": parser_kind, "config": config.strip() or None,
            "location": location.strip() or None,
            "enabled": 1,
        })
        st.success(f"Added source: {name.strip()}")
        st.rerun()

st.divider()

# ============================================================ Sources list
styles.asection("Configured sources", "layers")

if sdf.empty:
    st.info("No sources yet. Add one above.")
    st.stop()

cs1, cs2 = st.columns([1, 1])
with cs1:
    if st.button("Sync all enabled", type="primary", icon=":material/refresh:",
                 disabled=not auth.CRAWLER_ENABLED):
        with st.spinner("Crawling all enabled sources…"):
            for _, r in sdf[sdf["enabled"] == 1].iterrows():
                crawler.crawl_source(int(r["id"]))
        st.success("Crawled enabled sources.")
        st.rerun()
with cs2:
    respect = st.toggle("Respect robots.txt", value=True, key="src_respect_robots",
                        help="Disable only for sites you have explicit permission to crawl.")

# Per-source rows.
for _, r in sdf.iterrows():
    sid = int(r["id"])
    with st.container(border=True):
        h1, h2, h3 = st.columns([4, 2, 2], vertical_alignment="center")
        with h1:
            label = r["name"] + (" · disabled" if not r["enabled"] else "")
            st.markdown(f"**{label}**")
            meta_bits = [f"[{r['url']}]({r['url']})", f"`{r['parser_kind']}`"]
            if r.get("location"):
                meta_bits.append(f":material/location_on: {r['location']}")
            st.caption(" · ".join(meta_bits))
            if r.get("last_status"):
                color = "#16a34a" if str(r["last_status"]).startswith("OK") else "#dc2626"
                st.markdown(
                    f"<span style='color:{color};font-size:13px;font-weight:650'>"
                    f"{r['last_status']}</span>"
                    + (f"<span style='color:#9aa3b2;font-size:12px;margin-left:8px'>"
                       f"{r['last_run_at']}</span>" if r.get("last_run_at") else ""),
                    unsafe_allow_html=True,
                )
        with h2:
            new_enabled = st.toggle("Enabled", value=bool(r["enabled"]),
                                    key=f"src_en_{sid}")
            if new_enabled != bool(r["enabled"]):
                db.update_crawl_source(sid, {"enabled": int(new_enabled)})
                st.rerun()
        with h3:
            b1, b2, b3 = st.columns(3)
            with b1:
                with st.popover(":material/edit_location:", use_container_width=True,
                                help="Edit location for this source"):
                    new_loc = st.text_input(
                        "Location", value=r.get("location") or "",
                        key=f"src_loc_{sid}",
                        placeholder="e.g. Coral Springs, FL",
                    )
                    apply_loc = st.button("Save", key=f"src_loc_save_{sid}",
                                          type="primary", width="stretch")
                    if apply_loc:
                        db.update_crawl_source(sid, {"location": new_loc.strip() or None})
                        # Backfill existing crawled listings for this source so
                        # the new location shows up on the storefront immediately.
                        with db.get_conn() as conn:
                            conn.execute(
                                "UPDATE listings SET location = ? WHERE crawl_source_id = ?",
                                (new_loc.strip() or None, sid),
                            )
                        st.success("Location updated and applied to existing listings.")
                        st.rerun()
            with b2:
                if st.button("Sync", key=f"src_sync_{sid}",
                             icon=":material/refresh:", width="stretch",
                             disabled=not auth.CRAWLER_ENABLED):
                    with st.spinner(f"Crawling {r['name']}…"):
                        result = crawler.crawl_source(
                            sid, respect_robots=st.session_state.get("src_respect_robots", True)
                        )
                    if result.status == "ok":
                        st.success(
                            f"{result.new_listings} new, "
                            f"{result.updated_listings} updated "
                            f"({result.fetched_pages} page(s))."
                        )
                    else:
                        st.error(result.error or "Crawl failed.")
                    st.rerun()
            with b3:
                if st.button(":material/delete:", key=f"src_del_{sid}",
                             help="Delete source", width="stretch"):
                    db.delete_crawl_source(sid)
                    st.success("Deleted.")
                    st.rerun()

st.divider()

# ============================================================ Recent runs
styles.asection("Recent crawl runs", "bell")
runs = db.fetch_crawl_runs_df(limit=20)
if runs.empty:
    st.caption("No runs yet. Hit **Sync** on a source to crawl it.")
else:
    show = runs.copy()
    src_name = {int(r["id"]): r["name"] for _, r in sdf.iterrows()}
    show["Source"] = show["source_id"].map(src_name).fillna("(deleted)")
    show["When"] = pd.to_datetime(show["finished_at"], errors="coerce").dt.strftime("%b %d, %Y %H:%M")
    show = show[["When", "Source", "status", "fetched_pages",
                 "new_listings", "updated_listings", "error_message"]]
    show.columns = ["When", "Source", "Status", "Pages",
                    "New listings", "Updated", "Error"]
    st.dataframe(show, width="stretch", hide_index=True)
