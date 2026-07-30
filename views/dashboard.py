"""Admin dashboard — inventory health at a glance."""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from lib import auth, crawler, db, scoring, styles
from lib.icons import icon
from lib.ui import money

styles.hero("Inventory dashboard", "Live stats across your listings.",
            icon_svg=icon("dashboard", 30, "#ffffff"))

if not auth.require_admin():
    st.stop()

new_requests = db.count_inquiries("New")
if new_requests:
    st.info(f":material/inbox: You have **{new_requests}** new customer request(s) — "
            "review them on the **Requests** page.")

# ---------------------------------------------------------------- refresh CTA
# One-click sync of every enabled crawl source. Static-mode only (no headless
# toggle) because Playwright doesn't run in the Fly container — for headless
# crawls, go to Admin → Sources and enable the deep-crawl toggle there.
_sdf = db.fetch_crawl_sources_df()
_enabled = _sdf[_sdf["enabled"] == 1] if not _sdf.empty else _sdf
_runs = db.fetch_crawl_runs_df(limit=1) if not _sdf.empty else None
_last = _runs.iloc[0] if (_runs is not None and not _runs.empty) else None
_meta_bits = [f"{len(_enabled)} enabled source(s)"]
if _last is not None:
    when = pd.to_datetime(_last["finished_at"], errors="coerce")
    if pd.notna(when):
        _meta_bits.append(f"last synced {when.strftime('%b %-d, %H:%M')}")
_meta_line = " · ".join(_meta_bits)

with st.container(border=True, key="dash_sync_card"):
    lc, rc = st.columns([5, 2], vertical_alignment="center")
    with lc:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:14px;'>"
            f"<div style='width:44px;height:44px;border-radius:12px;background:#eef4ff;"
            f"border:1px solid #d8e6fb;display:flex;align-items:center;justify-content:center;'>"
            f"{icon('refresh', 22, '#2E8BFF')}</div>"
            f"<div><div style='font-size:15px;font-weight:750;color:var(--ll-ink)'>"
            f"Refresh inventory</div>"
            f"<div style='font-size:12.5px;color:#6b7686;margin-top:2px'>{_meta_line}</div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    with rc:
        sync_clicked = st.button(
            "Sync all sources", type="primary", width="stretch",
            icon=":material/refresh:", key="dash_sync_all",
            disabled=not auth.CRAWLER_ENABLED or _enabled.empty,
        )
    if sync_clicked:
        totals = {"new": 0, "updated": 0, "pages": 0, "errors": []}
        with st.spinner("Crawling all enabled sources…"):
            for _, r in _enabled.iterrows():
                res = crawler.crawl_source(int(r["id"]))
                if res.status == "ok":
                    totals["new"] += res.new_listings
                    totals["updated"] += res.updated_listings
                    totals["pages"] += res.fetched_pages
                else:
                    totals["errors"].append(f"{r['name']}: {res.error}")
        if totals["errors"]:
            st.error("Some sources failed:\n\n- " + "\n- ".join(totals["errors"]))
        else:
            st.success(
                f"Synced {len(_enabled)} source(s): "
                f"{totals['new']} new, {totals['updated']} updated "
                f"({totals['pages']} pages fetched)."
            )
        st.rerun()

df = scoring.enrich(db.fetch_df(active_only=False))
if df.empty:
    st.info("No listings yet. Add some on **Manage Listings** or **Bulk CSV Upload**.")
    st.stop()

active = df[df["status"] == "active"]
_disc = active["discount_percent"].dropna()

styles.metric_cards([
    ("layers", len(df), "Total listings", "#0E2A47"),
    ("check-circle", len(active), "Active", "#16a34a"),
    ("dollar-sign", money(active["monthly_payment"].dropna().mean()), "Avg monthly", "#0ea5e9"),
    ("percent", f"{_disc.mean():.1f}%" if not _disc.empty else "—", "Avg discount", "#f59e0b"),
    ("tag", active["make"].nunique(), "Brands", "#db2777"),
])

st.divider()

left, right = st.columns(2, gap="large")

with left:
    styles.asection("Listings by make", "tag")
    by_make = (df.groupby("make").size().reset_index(name="count")
               .sort_values("count", ascending=False))
    chart = (alt.Chart(by_make).mark_bar(cornerRadiusEnd=4, color="#2E8BFF")
             .encode(x=alt.X("count:Q", title="Listings"),
                     y=alt.Y("make:N", sort="-x", title=None),
                     tooltip=["make", "count"]))
    st.altair_chart(chart, use_container_width=True)

with right:
    styles.asection("Deal type mix", "layers", "#0ea5e9")
    by_type = df.groupby("deal_type").size().reset_index(name="count")
    pie = (alt.Chart(by_type).mark_arc(innerRadius=55)
           .encode(theta="count:Q",
                   color=alt.Color("deal_type:N", title="Deal type",
                                   scale=alt.Scale(scheme="purpleblue")),
                   tooltip=["deal_type", "count"]))
    st.altair_chart(pie, use_container_width=True)

left2, right2 = st.columns(2, gap="large")

with left2:
    styles.asection("Avg monthly by body type", "dollar-sign", "#16a34a")
    by_body = (active.dropna(subset=["monthly_payment"])
               .groupby("body_type")["monthly_payment"].mean().reset_index())
    if not by_body.empty:
        chart2 = (alt.Chart(by_body).mark_bar(cornerRadiusEnd=4, color="#0ea5e9")
                  .encode(x=alt.X("monthly_payment:Q", title="Avg $/mo"),
                          y=alt.Y("body_type:N", sort="-x", title=None),
                          tooltip=["body_type", alt.Tooltip("monthly_payment:Q", format="$.0f")]))
        st.altair_chart(chart2, use_container_width=True)
    else:
        st.caption("No monthly data.")

with right2:
    styles.asection("Value map — monthly vs MSRP", "percent", "#db2777")
    scat = active.dropna(subset=["monthly_payment", "msrp"])
    if not scat.empty:
        chart3 = (alt.Chart(scat).mark_circle(size=120, opacity=0.7)
                  .encode(x=alt.X("msrp:Q", title="MSRP", scale=alt.Scale(zero=False)),
                          y=alt.Y("monthly_payment:Q", title="Monthly $"),
                          color=alt.Color("deal_type:N", scale=alt.Scale(scheme="purpleblue")),
                          tooltip=["make", "model", alt.Tooltip("msrp:Q", format="$,.0f"),
                                   alt.Tooltip("monthly_payment:Q", format="$,.0f"),
                                   "deal_score"]))
        st.altair_chart(chart3, use_container_width=True)
    else:
        st.caption("No data for value map.")

st.divider()
styles.asection("Best values (by deal score)", "star", "#7c3aed")
top = (active.dropna(subset=["deal_score"]).sort_values("deal_score", ascending=False).head(10))
if not top.empty:
    show = top[["make", "model", "year", "deal_type", "monthly_payment",
                "effective_monthly", "percent_of_msrp", "deal_score", "rating"]].copy()
    show.columns = ["Make", "Model", "Year", "Type", "Monthly", "Eff/mo", "% MSRP", "Score", "Rating"]
    st.dataframe(
        show, width="stretch", hide_index=True,
        column_config={
            "Monthly": st.column_config.NumberColumn(format="$%d"),
            "Eff/mo": st.column_config.NumberColumn(format="$%.0f"),
            "% MSRP": st.column_config.NumberColumn(format="%.2f%%"),
            "Score": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d"),
        },
    )
