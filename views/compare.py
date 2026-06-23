"""Side-by-side comparison of selected deals."""
from __future__ import annotations

import streamlit as st

from lib import db, scoring, styles
from lib.icons import icon
from lib.ui import comparison_frame, title_for

styles.hero("Compare deals", "Line up to four cars side-by-side on the numbers that matter.",
            icon_svg=icon("compare_arrows", 30, "#ffffff"))

df = scoring.enrich(db.fetch_df(active_only=True))
if df.empty:
    st.warning("No active listings to compare yet.")
    st.stop()

df["label"] = df.apply(lambda r: f"{title_for(r)} — {r.get('trim') or ''} ({r['deal_type']})", axis=1)
choices = df["label"].tolist()

# Pre-select anything the shopper ticked "Compare" on the Browse page.
picked_ids = [int(k[4:]) for k, v in st.session_state.items() if k.startswith("cmp_") and v]
default = df[df["id"].isin(picked_ids)]["label"].tolist()[:4]
if not default:
    default = choices[:2] if len(choices) >= 2 else choices

picked = st.multiselect("Pick deals to compare (up to 4)", choices, max_selections=4, default=default)

if not picked:
    st.info("Select two or more deals above to see a side-by-side comparison.")
    st.stop()

sub = df[df["label"].isin(picked)]
comp = comparison_frame(sub)
st.dataframe(comp, width="stretch", height=(len(comp) + 1) * 35 + 3)

st.caption("Lower **% of MSRP/mo** is better — at or below ~1% is a strong lease. "
           "Effective monthly folds any money down into the payment.")
