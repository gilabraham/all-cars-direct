"""Customer-facing deal browser with rich filtering."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import db, scoring, styles
from lib.deal_detail import show_detail
from lib.icons import body_icon_html, icon, make_icon_html
from lib.ui import card_html

# Toast confirming a just-submitted deal request (set inside the detail dialog).
if "req_toast" in st.session_state:
    st.toast(st.session_state.pop("req_toast"), icon=":material/check_circle:")

df = scoring.enrich(db.fetch_df(active_only=True))

if df.empty:
    st.warning("No active listings yet. Add inventory from the **Admin → Manage Listings** page.")
    st.stop()


# URL params ↔ filter state.
#
# - On first load (per browser session), we hydrate session_state from any
#   filter-related URL params. This handles homepage-tile clicks
#   (?body=SUV) AND browser refresh (everything you had ticked stays
#   ticked).
# - After the user-facing widgets render, we PUBLISH session_state back to the
#   URL so subsequent refreshes or copy-paste-share preserve the full state.
_MULTI_FILTERS = (
    ("body", "flt_body_"),
    ("make", "flt_make_"),
    ("model", "flt_model_"),
    ("fuel", "flt_fuel_"),
    ("deal", "flt_deal_"),
)


def _consume_query_filters_once():
    if st.session_state.get("_filters_initialized"):
        return
    st.session_state["_filters_initialized"] = True
    qp = dict(st.query_params)
    if not qp:
        return
    if "q" in qp:
        st.session_state["flt_q"] = qp["q"]
    if "sort" in qp:
        st.session_state["flt_sort"] = qp["sort"]
    if qp.get("featured") == "1":
        st.session_state["flt_feat"] = True
    for key, prefix in _MULTI_FILTERS:
        if key in qp:
            for val in qp[key].split(","):
                v = val.strip()
                if v:
                    st.session_state[f"{prefix}{v}"] = True


def _publish_query_filters():
    new_qp: dict[str, str] = {}
    if st.session_state.get("flt_q"):
        new_qp["q"] = st.session_state["flt_q"]
    sort_v = st.session_state.get("flt_sort")
    if sort_v and sort_v != "Featured":
        new_qp["sort"] = sort_v
    if st.session_state.get("flt_feat"):
        new_qp["featured"] = "1"
    for key, prefix in _MULTI_FILTERS:
        vals = [
            k[len(prefix):] for k in st.session_state
            if k.startswith(prefix) and st.session_state[k]
        ]
        if vals:
            new_qp[key] = ",".join(sorted(vals))
    current = {k: v for k, v in st.query_params.items()}
    if current != new_qp:
        st.query_params.clear()
        for k, v in new_qp.items():
            st.query_params[k] = v


_consume_query_filters_once()


# Callbacks run before the rerun, so we avoid a second st.rerun() (which makes
# the fixed nav flash). One rerun = no flicker.
def _clear_one(key: str):
    # Setting the widget's session_state explicitly (rather than deleting it)
    # reliably unchecks the corresponding checkbox/toggle on the next rerun.
    if key == "flt_q":
        st.session_state[key] = ""
    else:
        st.session_state[key] = False


# Prefixes for the multi-value checkbox filters (each checkbox writes to
# ``flt_<prefix>_<value>``).
_FILTER_PREFIXES = ("flt_deal_", "flt_make_", "flt_model_",
                    "flt_body_", "flt_fuel_")


def _clear_all_filters():
    """Reset every filter widget back to its default state.

    ``del st.session_state[key]`` does NOT reliably reset a widget that's
    still in the script — Streamlit keeps the prior value because the widget
    re-registers on the next render. Explicitly assigning False/empty/default
    triggers proper reconciliation.
    """
    # Multi-value checkboxes (one per option).
    for k in list(st.session_state.keys()):
        if any(k.startswith(p) for p in _FILTER_PREFIXES):
            st.session_state[k] = False
    # Single-value widgets.
    st.session_state["flt_q"] = ""
    st.session_state["flt_feat"] = False
    if "flt_cash" in st.session_state:
        st.session_state["flt_cash"] = True
    if "flt_sort" in st.session_state:
        st.session_state["flt_sort"] = "Featured"
    # Sliders use tuple/int defaults — deleting these is fine because the
    # next render will re-initialize them from the slider's default arg.
    for k in ("flt_year", "flt_monthly"):
        if k in st.session_state:
            del st.session_state[k]


def _page_delta(delta: int):
    st.session_state["browse_page"] = max(1, st.session_state.get("browse_page", 1) + delta)


def _close_mobile_filters():
    """Callback for the mobile-flyout close button. Using on_click (instead of
    inline ``st.rerun()``) keeps Streamlit's widget-state reconciliation
    intact — clicking ✕ now just dismisses the panel without disturbing any
    ``flt_*`` selections."""
    st.session_state["mobile_filters_open"] = False


def _open_mobile_filters():
    st.session_state["mobile_filters_open"] = True



# ===================== Filter / sort: precompute pools, counts, read state ====
SORT_OPTIONS = ["Featured", "Best deal score", "Lowest monthly", "Lowest effective monthly",
                "Lowest % of MSRP", "Newest year", "Make A–Z"]

makes = sorted(df["make"].dropna().unique().tolist())
body_types = sorted(df["body_type"].dropna().unique().tolist())
fuels = sorted(df["fuel_type"].dropna().unique().tolist())
yr_min, yr_max = int(df["year"].min()), int(df["year"].max())
# Monthly slider should range over ALL monthly-payment fields so headless-
# crawled rows (which populate lease_monthly / finance_monthly but not the
# legacy monthly_payment column) aren't silently clipped out at load.
_monthly_cols = [c for c in ("monthly_payment", "lease_monthly", "finance_monthly")
                 if c in df.columns]
monthly_series = pd.concat([df[c].dropna() for c in _monthly_cols]) \
    if _monthly_cols else pd.Series([], dtype="float64")
has_monthly = not monthly_series.empty
m_min = int(monthly_series.min()) if has_monthly else 0
m_max = int(monthly_series.max()) + 1 if has_monthly else 0

# Counts so each filter option shows its inventory count ("Toyota (8)").
make_counts = df.groupby("make").size().to_dict()
body_counts = df.groupby("body_type").size().to_dict()
fuel_counts = df.groupby("fuel_type").size().to_dict()
# Deal-type counts derive from which per-type pricing fields are populated,
# not the listing's nominal ``deal_type`` column — a single listing usually
# offers lease + finance + cash simultaneously after a headless crawl.
deal_counts = {
    "Lease": int(df["lease_monthly"].notna().sum()) if "lease_monthly" in df.columns else 0,
    "Finance": int(df["finance_monthly"].notna().sum()) if "finance_monthly" in df.columns else 0,
    "Cash": int(df["selling_price"].notna().sum()) if "selling_price" in df.columns else 0,
}
# Backfill from the nominal ``deal_type`` column for legacy/CSV-uploaded
# rows that don't have per-type columns populated.
if not any(deal_counts.values()) and "deal_type" in df.columns:
    deal_counts = df.groupby("deal_type").size().to_dict()

# Read filter values from session state first so we can sort/filter before
# rendering the layout. Selections are per-option checkboxes with keys like
# flt_make_<value>; aggregate to lists.
q = st.session_state.get("flt_q", "") or ""
sort_by = st.session_state.get("flt_sort", "Featured")
sel_years = st.session_state.get("flt_year", (yr_min, yr_max)) if yr_min < yr_max else (yr_min, yr_max)
sel_monthly = st.session_state.get("flt_monthly", m_max) if has_monthly else None
include_cash = st.session_state.get("flt_cash", True)
only_featured = st.session_state.get("flt_feat", False)

deal_types = [d for d in db.DEAL_TYPES if st.session_state.get(f"flt_deal_{d}")]
sel_makes = [m for m in makes if st.session_state.get(f"flt_make_{m}")]
sel_body = [b for b in body_types if st.session_state.get(f"flt_body_{b}")]
sel_fuel = [fu for fu in fuels if st.session_state.get(f"flt_fuel_{fu}")]

model_pool = df[df["make"].isin(sel_makes)] if sel_makes else df
models = sorted(model_pool["model"].dropna().unique().tolist())
model_counts = model_pool.groupby("model").size().to_dict()
sel_models = [m for m in models if st.session_state.get(f"flt_model_{m}")]

# Sort options by inventory count descending (most popular first) for the
# checkbox lists — Carvana convention.
makes_sorted = sorted(makes, key=lambda x: -make_counts.get(x, 0))
body_sorted = sorted(body_types, key=lambda x: -body_counts.get(x, 0))
fuel_sorted = sorted(fuels, key=lambda x: -fuel_counts.get(x, 0))
models_sorted = sorted(models, key=lambda x: -model_counts.get(x, 0))

# ----------------------------------------------------------- apply filters
f = df.copy()
if q:
    ql = q.lower()
    hay = (f["make"].fillna("") + " " + f["model"].fillna("") + " " + f["trim"].fillna("") + " "
           + f["fuel_type"].fillna("") + " " + f["body_type"].fillna("") + " "
           + f["location"].fillna("") + " " + f["dealer_name"].fillna("")).str.lower()
    f = f[hay.str.contains(ql, na=False)]
if deal_types:
    # Match by *availability* of the per-deal-type pricing fields, not the
    # listing's nominal ``deal_type`` column. A car with ``lease_monthly``
    # populated qualifies as "Lease" even if its ``deal_type`` says "Cash".
    masks = []
    if "Lease" in deal_types and "lease_monthly" in f.columns:
        masks.append(f["lease_monthly"].notna())
    if "Finance" in deal_types and "finance_monthly" in f.columns:
        masks.append(f["finance_monthly"].notna())
    if "Cash" in deal_types and "selling_price" in f.columns:
        masks.append(f["selling_price"].notna())
    if masks:
        combined = masks[0]
        for m in masks[1:]:
            combined = combined | m
        f = f[combined]
    else:
        # Fallback for legacy rows without per-type columns.
        f = f[f["deal_type"].isin(deal_types)]
if sel_makes:
    f = f[f["make"].isin(sel_makes)]
if sel_models:
    f = f[f["model"].isin(sel_models)]
if sel_body:
    f = f[f["body_type"].isin(sel_body)]
if sel_fuel:
    f = f[f["fuel_type"].isin(sel_fuel)]
f = f[(f["year"] >= sel_years[0]) & (f["year"] <= sel_years[1])]
if sel_monthly is not None:
    is_cash = f["deal_type"] == "Cash"
    # A row passes if ANY of its monthly-payment fields is within the cap.
    # NaN comparisons are False, so missing fields don't accidentally pass.
    within = pd.Series(False, index=f.index)
    for col in ("monthly_payment", "lease_monthly", "finance_monthly"):
        if col in f.columns:
            within = within | (f[col] <= sel_monthly)
    f = f[within | (is_cash if include_cash else False)]
if only_featured:
    f = f[f["featured"] == 1]

# ----------------------------------------------------------- card preference
# Tell card_html / show_detail which deal type the user is filtering for, so
# the badge + modal-default-tab match the filter. If the user ticked "Cash",
# Cash leads even when the listing also has lease/finance pricing. The raw
# checked set goes through too so cards can render multiple pills when the
# user opted into more than one deal type.
_priority = ["Lease", "Finance", "Cash"]
if deal_types:
    st.session_state["_card_deal_pref"] = (
        [d for d in _priority if d in deal_types]
        + [d for d in _priority if d not in deal_types]
    )
else:
    st.session_state["_card_deal_pref"] = _priority
st.session_state["_card_user_deals"] = list(deal_types)

# ----------------------------------------------------------- sort
if sort_by == "Featured":
    f = f.sort_values(["featured", "deal_score"], ascending=[False, False])
elif sort_by == "Best deal score":
    f = f.sort_values("deal_score", ascending=False, na_position="last")
elif sort_by == "Lowest monthly":
    f = f.sort_values("monthly_payment", ascending=True, na_position="last")
elif sort_by == "Lowest effective monthly":
    f = f.sort_values("effective_monthly", ascending=True, na_position="last")
elif sort_by == "Lowest % of MSRP":
    f = f.sort_values("percent_of_msrp", ascending=True, na_position="last")
elif sort_by == "Newest year":
    f = f.sort_values("year", ascending=False)
elif sort_by == "Make A–Z":
    f = f.sort_values(["make", "model"], ascending=True)
f = f.reset_index(drop=True)

total = len(f)

# Active-filter chips for the results bar — list of (label, session_state key
# to clear when the chip is dismissed).
chips: list[tuple[str, str]] = []
chips.extend((d, f"flt_deal_{d}") for d in deal_types)
chips.extend((m, f"flt_make_{m}") for m in sel_makes)
chips.extend((m, f"flt_model_{m}") for m in sel_models)
chips.extend((b, f"flt_body_{b}") for b in sel_body)
chips.extend((fu, f"flt_fuel_{fu}") for fu in sel_fuel)
if q:
    chips.append((f'"{q}"', "flt_q"))
if only_featured:
    chips.append(("Featured", "flt_feat"))

# ============================================ 2-col layout: rail | main =====
# Mobile-only: "Filter & sort" toggle button that opens the rail as a full-
# screen flyout. Hidden on desktop via CSS. State drives a marker element the
# CSS uses to flip the rail into overlay mode.
if "mobile_filters_open" not in st.session_state:
    st.session_state["mobile_filters_open"] = False

with st.container(key="mobile_filter_bar"):
    open_count = (len(sel_makes) + len(sel_body) + len(sel_fuel)
                  + len(sel_models) + len(deal_types)
                  + (1 if only_featured else 0) + (1 if q else 0))
    label = f"Filter & sort{f' ({open_count})' if open_count else ''}"
    st.button(label, key="open_mobile_filters",
              icon=":material/tune:", width="stretch", type="secondary",
              on_click=_open_mobile_filters)

# Marker so the CSS below can detect "open" state via :has() and morph the
# rail column into a fixed-position overlay.
if st.session_state.get("mobile_filters_open"):
    st.markdown(
        "<div class='ll-mobile-filters-marker' aria-hidden='true'></div>",
        unsafe_allow_html=True,
    )

rail_col, main_col = st.columns([1, 3.2], gap="large")

with rail_col:
    st.markdown(
        f"<h3 class='ll-rail-title' style='display:flex;align-items:center;gap:8px;margin:0 0 10px'>"
        f"{icon('layers', 18, '#0E2A47')} Filters</h3>",
        unsafe_allow_html=True,
    )

    def _lbl(name: str, n: int) -> str:
        return f"{name} ({n})" if n else name

    yr_default = (yr_min, yr_max) if yr_min < yr_max else None
    yr_active = yr_default and sel_years != yr_default

    def _check_list(values, counts, prefix: str) -> None:
        del counts  # counts no longer rendered in filter labels
        for v in values:
            st.checkbox(str(v), key=f"flt_{prefix}_{v}")

    def _check_list_with_icons(values, counts, prefix: str, icon_fn) -> None:
        del counts
        for v in values:
            c1, c2 = st.columns([1, 1], vertical_alignment="center", gap="small")
            with c1:
                st.checkbox(str(v), key=f"flt_{prefix}_{v}")
            with c2:
                st.markdown(icon_fn(v), unsafe_allow_html=True)

    with st.container(key="filterrail"):
        # Mobile-only: round ✕ button pinned to the top-right of the flyout.
        # Hidden on desktop via CSS. Uses ``on_click`` instead of inline
        # ``st.rerun()`` — st.rerun() called mid-script halts before the
        # filter widgets below render, and Streamlit then garbage-collects
        # their session state. on_click runs BEFORE the render flow, so all
        # widgets render and their selections survive.
        with st.container(key="mobile_filter_close"):
            st.button("Close", key="close_mobile_filters",
                      icon=":material/close:", help="Close filters",
                      on_click=_close_mobile_filters)

        with st.expander(_lbl("Deal type", len(deal_types)), expanded=bool(deal_types)):
            _check_list(db.DEAL_TYPES, deal_counts, "deal")

        if has_monthly:
            _price_active = (sel_monthly is not None and sel_monthly < m_max) or not include_cash
            with st.expander("Price", expanded=bool(_price_active)):
                st.slider("Max monthly price ($)", m_min, m_max, m_max, step=10,
                          key="flt_monthly")
                st.toggle("Include cash deals", value=True, key="flt_cash")

        with st.expander(_lbl("Make", len(sel_makes)), expanded=bool(sel_makes)):
            _check_list_with_icons(makes_sorted, make_counts, "make", make_icon_html)

        with st.expander(_lbl("Model", len(sel_models)), expanded=bool(sel_models)):
            _check_list(models_sorted, model_counts, "model")

        with st.container(key="bodytype_filter"):
            with st.expander(_lbl("Body type", len(sel_body)), expanded=bool(sel_body)):
                _check_list_with_icons(body_sorted, body_counts, "body", body_icon_html)

        with st.expander(_lbl("Fuel", len(sel_fuel)), expanded=bool(sel_fuel)):
            _check_list(fuel_sorted, fuel_counts, "fuel")

        if yr_min < yr_max:
            with st.expander("Year", expanded=bool(yr_active)):
                st.slider("Year", yr_min, yr_max, (yr_min, yr_max),
                          key="flt_year", label_visibility="collapsed")

        with st.expander("Search & flags", expanded=bool(q or only_featured)):
            st.text_input("Search", key="flt_q",
                          placeholder="e.g. RAV4, electric, Miami",
                          label_visibility="collapsed")
            st.toggle(":material/star: Featured only", key="flt_feat")

    st.button("Clear all filters", icon=":material/restart_alt:", key="rail_clear",
              width="stretch", on_click=_clear_all_filters)

    # Mobile-only: sticky "Apply filters · N results" CTA pinned to the bottom
    # of the flyout. Filters are already applied (each checkbox triggers a
    # rerun), so this button just commits the changes by dismissing the
    # flyout. Uses on_click for the same reason the ✕ button does — see
    # ``_close_mobile_filters``. Hidden on desktop via CSS.
    with st.container(key="mobile_filter_apply"):
        apply_label = f"Apply filters · {total} result{'s' if total != 1 else ''}"
        st.button(apply_label, key="apply_mobile_filters",
                  icon=":material/check:", width="stretch", type="primary",
                  on_click=_close_mobile_filters)


with main_col:
    # ----------------------- results bar (count + chips + sort)
    hc1, hc2 = st.columns([3, 1.2])
    with hc1:
        st.markdown(
            f"<div class='ll-results-count'>{total} deal{'s' if total != 1 else ''}"
            f" <small>available</small></div>",
            unsafe_allow_html=True,
        )
    with hc2:
        st.selectbox("Sort by", SORT_OPTIONS, key="flt_sort")

    # Active filter chips — click × to remove that filter.
    if chips:
        with st.container(key="active_chips"):
            for label, ck in chips:
                st.button(f"✕ {label}", key=f"chip_{ck}",
                          on_click=_clear_one, args=(ck,))

    st.markdown("<div class='ll-results-divider'></div>", unsafe_allow_html=True)

    if total == 0:
        st.info("No deals match your filters. Try widening your search or clearing filters.")
        st.stop()

    # ----------------------- pagination + card grid
    per_page = 12
    pages = (total - 1) // per_page + 1
    if "browse_page" not in st.session_state:
        st.session_state.browse_page = 1
    st.session_state.browse_page = min(st.session_state.browse_page, pages)
    start = (st.session_state.browse_page - 1) * per_page
    page_df = f.iloc[start:start + per_page]

    cols_per_row = 3
    records = page_df.to_dict(orient="records")
    for i in range(0, len(records), cols_per_row):
        cols = st.columns(cols_per_row, gap="medium")
        for col, row in zip(cols, records[i:i + cols_per_row]):
            with col:
                with st.container(border=True, key=f"cardwrap_{row['id']}"):
                    st.markdown(card_html(row), unsafe_allow_html=True)
                    if st.button("View details", key=f"detail_{row['id']}",
                                 width="stretch", type="primary"):
                        show_detail(row)

    if pages > 1:
        st.divider()
        pcols = st.columns([1, 2, 1])
        with pcols[0]:
            st.button(":material/chevron_left: Prev",
                      disabled=st.session_state.browse_page <= 1,
                      width="stretch", on_click=_page_delta, args=(-1,))
        with pcols[1]:
            st.markdown(
                f"<div style='text-align:center;padding-top:6px;color:#6b7280'>"
                f"Page {st.session_state.browse_page} of {pages} · "
                f"showing {len(page_df)} of {total}</div>",
                unsafe_allow_html=True,
            )
        with pcols[2]:
            st.button("Next :material/chevron_right:",
                      disabled=st.session_state.browse_page >= pages,
                      width="stretch", on_click=_page_delta, args=(1,))

# Keep the browser URL in sync with the active filters so a refresh (or
# copy/paste/share) preserves exactly what is selected.
_publish_query_filters()
