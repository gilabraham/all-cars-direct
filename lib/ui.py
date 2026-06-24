"""Formatting helpers and HTML card rendering for the browse view."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

from . import scoring
from .icons import icon
from .images import image_src

DEAL_PRIORITY = ("Lease", "Finance", "Cash")


def featured_deal_for(row) -> str:
    """Pick which deal type a card should lead with — defers to the user's
    current filter selection (``_card_deal_pref`` in session state, set by
    the browse view) so ticking "Cash" makes every card show Cash even
    when the row also has lease/finance pricing."""
    available = available_deal_types(row)
    pref = st.session_state.get("_card_deal_pref", DEAL_PRIORITY)
    for d in pref:
        if d in available:
            return d
    return available[0] if available else "Cash"


def _isna(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def money(x, dash="—") -> str:
    if _isna(x):
        return dash
    try:
        return f"${float(x):,.0f}"
    except (TypeError, ValueError):
        return dash


def num(x, dash="—") -> str:
    if _isna(x):
        return dash
    try:
        return f"{float(x):,.0f}"
    except (TypeError, ValueError):
        return dash


def pct(x, dash="—") -> str:
    if _isna(x):
        return dash
    try:
        return f"{float(x):.1f}%"
    except (TypeError, ValueError):
        return dash


def deal_type_color(deal_type: str) -> str:
    return {
        "Lease": "#2E8BFF",
        "Finance": "#0ea5e9",
        "Cash": "#10b981",
    }.get(deal_type or "Lease", "#2E8BFF")


def title_for(row) -> str:
    yr = row.get("year")
    yr = str(int(yr)) if not _isna(yr) else ""
    return f"{yr} {row.get('make','')} {row.get('model','')}".strip()


def _mf(x):
    return f"{float(x):.5f}" if (not _isna(x) and x) else "—"


def comparison_frame(sub) -> pd.DataFrame:
    """Build a side-by-side comparison DataFrame (metrics x deals, all strings)."""
    rows = {
        "Deal type": lambda r: r.get("deal_type") or "—",
        "Trim": lambda r: r.get("trim") or "—",
        "Body / Fuel": lambda r: f"{r.get('body_type') or '—'} / {r.get('fuel_type') or '—'}",
        "Monthly": lambda r: money(r.get("monthly_payment")),
        "Effective monthly": lambda r: money(r.get("effective_monthly")),
        "Due at signing": lambda r: money(r.get("down_payment")),
        "Term (mo)": lambda r: num(r.get("term_months")),
        "Miles/yr": lambda r: num(r.get("annual_mileage")),
        "MSRP": lambda r: money(r.get("msrp")),
        "Selling price": lambda r: money(r.get("selling_price")),
        "Discount": lambda r: pct(r.get("discount_percent")),
        "% of MSRP/mo": lambda r: pct(r.get("percent_of_msrp")),
        "Money factor": lambda r: _mf(r.get("money_factor")),
        "Residual": lambda r: pct(r.get("residual_percent")),
        "Deal score": lambda r: f"{int(r['deal_score'])}/100" if not _isna(r.get("deal_score")) else "—",
        "Rating": lambda r: r.get("rating") or "—",
        "Location": lambda r: r.get("location") or "—",
    }
    table = {}
    for _, r in sub.iterrows():
        table[title_for(r)] = {metric: fn(r) for metric, fn in rows.items()}
    out = pd.DataFrame(table).astype(str)
    out.index.name = "Metric"
    return out


def available_deal_types(row) -> list[str]:
    """Return the deal types actually offered for this listing — derived from
    which per-deal-type pricing fields the headless crawl captured.
    Used for both filtering ("show only lease deals") and card rendering
    ("which offer should the card lead with")."""
    out = []
    if not _isna(row.get("lease_monthly")):
        out.append("Lease")
    if not _isna(row.get("finance_monthly")):
        out.append("Finance")
    # Cash is universal — every listing has a selling/cash price.
    if not _isna(row.get("selling_price")) or not _isna(row.get("cash_price")):
        out.append("Cash")
    # Fall back to the listing's nominal deal_type field (covers legacy /
    # CSV-uploaded rows that don't have the per-type columns populated).
    if not out:
        dt = row.get("deal_type")
        if dt:
            out.append(dt)
    return out


def card_html(row) -> str:
    """Build a single deal card. The featured offer follows the user's
    current deal-type filter via :func:`featured_deal_for` — ticking
    "Cash" makes every card lead with Cash pricing."""
    available = available_deal_types(row)
    featured = featured_deal_for(row)
    dt_color = deal_type_color(featured)
    rating_label, rating_color = scoring.rating(
        row.get("monthly_payment"), row.get("down_payment"),
        row.get("term_months"), row.get("msrp"),
    )
    img = image_src(row.get("make"), row.get("model"), row.get("year"), row.get("image_url"))
    title = title_for(row)

    sub_parts = [str(p) for p in (row.get("trim"), row.get("body_type"), row.get("fuel_type")) if p]
    subtitle = " · ".join(sub_parts)

    fav_html = (
        f"<span class='ll-card-fav'>{icon('star', 13, '#f59e0b', fill='#f59e0b')}</span>"
        if int(row.get("featured") or 0) else ""
    )

    # ---- Primary price (the featured deal type) + a one-line spec.
    if featured == "Lease":
        amt = row.get("lease_monthly")
        term = row.get("lease_term_months")
        down = row.get("lease_down_payment")
        amount = (
            f"<span class='ll-card-amt'>{money(amt)}</span>"
            f"<span class='ll-card-unit'>/mo lease</span>"
        )
        bits = []
        if not _isna(term):
            bits.append(f"{int(term)} mo")
        if not _isna(down):
            bits.append(f"{money(down)} due")
        secondary = " · ".join(bits)
    elif featured == "Finance":
        amt = row.get("finance_monthly")
        term = row.get("finance_term_months")
        down = row.get("finance_down_payment")
        apr = row.get("finance_apr")
        amount = (
            f"<span class='ll-card-amt'>{money(amt)}</span>"
            f"<span class='ll-card-unit'>/mo finance</span>"
        )
        bits = []
        if not _isna(term):
            bits.append(f"{int(term)} mo")
        if not _isna(down):
            bits.append(f"{money(down)} down")
        if not _isna(apr):
            bits.append(f"{apr:.2f}% APR")
        secondary = " · ".join(bits)
    else:  # Cash
        # ``NaN or x`` returns NaN in Python (NaN is truthy), so reach for the
        # explicit isna check rather than the ``or`` shortcut — only 4 of 95
        # headless-crawled rows have ``cash_price`` set; the rest fall back
        # to the dealer-page ``selling_price``.
        cash_v = (row.get("cash_price")
                  if not _isna(row.get("cash_price"))
                  else row.get("selling_price"))
        amount = (
            f"<span class='ll-card-amt'>{money(cash_v)}</span>"
            f"<span class='ll-card-unit'>cash price</span>"
        )
        bits = []
        if not _isna(row.get("msrp")):
            bits.append(f"MSRP {money(row.get('msrp'))}")
        disc = scoring.discount_percent(cash_v, row.get("msrp"))
        if disc is not None:
            bits.append(f"{pct(disc)} off")
        secondary = " · ".join(bits)

    # ---- "Also available" mini-row for the non-featured deal types.
    alts = [d for d in available if d != featured]
    alt_bits = []
    for d in alts:
        if d == "Lease" and not _isna(row.get("lease_monthly")):
            alt_bits.append(f"Lease {money(row.get('lease_monthly'))}/mo")
        elif d == "Finance" and not _isna(row.get("finance_monthly")):
            alt_bits.append(f"Finance {money(row.get('finance_monthly'))}/mo")
        elif d == "Cash":
            cv = (row.get("cash_price")
                  if not _isna(row.get("cash_price"))
                  else row.get("selling_price"))
            if not _isna(cv):
                alt_bits.append(f"Cash {money(cv)}")
    alt_line = (
        f"<div class='ll-card-alts'>Also: {' · '.join(alt_bits)}</div>"
        if alt_bits else ""
    )

    html = f"""
    <div class='ll-card'>
      <div class='ll-card-media'>
        <img src='{img}' alt='{title}'/>
        <span class='ll-card-type' style='background:{dt_color}'>{featured}</span>
        {fav_html}
      </div>
      <div class='ll-card-body'>
        <div class='ll-card-title'>{title}</div>
        <div class='ll-card-sub'>{subtitle}</div>
        <div class='ll-card-price'>{amount}</div>
        <div class='ll-card-spec'>{secondary}</div>
        {alt_line}
      </div>
      <div class='ll-card-foot'>
        <span class='ll-card-loc'>{icon('location_on', 13, '#6b7280')} {row.get('location') or '—'}</span>
        <span class='ll-card-rate'>
          <span class='dot' style='background:{rating_color}'></span>
          <span class='lab' style='color:{rating_color}'>{rating_label}</span>
        </span>
      </div>
    </div>
    """
    # Collapse to a single line — indented multi-line HTML otherwise gets
    # parsed as a Markdown code block and rendered as literal text.
    return "".join(line.strip() for line in html.splitlines())
