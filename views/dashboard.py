"""Admin dashboard — inventory health at a glance."""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from lib import auth, db, scoring, styles
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
