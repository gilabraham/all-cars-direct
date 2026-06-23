"""Formatting helpers and HTML card rendering for the browse view."""
from __future__ import annotations

import math

import pandas as pd

from . import scoring
from .icons import icon
from .images import image_src


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


def card_html(row) -> str:
    """Build a single deal card as an HTML string (Carvana-style)."""
    deal_type = row.get("deal_type") or "Lease"
    dt_color = deal_type_color(deal_type)
    rating_label, rating_color = scoring.rating(
        row.get("monthly_payment"), row.get("down_payment"),
        row.get("term_months"), row.get("msrp"),
    )
    img = image_src(row.get("make"), row.get("model"), row.get("year"), row.get("image_url"))
    title = title_for(row)

    # Subtitle: trim · body · fuel
    sub_parts = [str(p) for p in (row.get("trim"), row.get("body_type"), row.get("fuel_type")) if p]
    subtitle = " · ".join(sub_parts)

    fav_html = (
        f"<span class='ll-card-fav'>{icon('star', 13, '#f59e0b', fill='#f59e0b')}</span>"
        if int(row.get("featured") or 0) else ""
    )

    # Price + compact secondary spec line per deal type.
    if deal_type == "Cash":
        amount = (
            f"<span class='ll-card-amt'>{money(row.get('selling_price'))}</span>"
            f"<span class='ll-card-unit'>cash price</span>"
        )
        bits = [f"MSRP {money(row.get('msrp'))}"]
        disc = scoring.discount_percent(row.get("selling_price"), row.get("msrp"))
        if disc is not None:
            bits.append(f"{pct(disc)} off")
        secondary = " · ".join(bits)
    elif deal_type == "Finance":
        amount = (
            f"<span class='ll-card-amt'>{money(row.get('monthly_payment'))}</span>"
            f"<span class='ll-card-unit'>/mo finance</span>"
        )
        bits = []
        if not _isna(row.get("down_payment")):
            bits.append(f"{money(row.get('down_payment'))} down")
        if not _isna(row.get("term_months")):
            bits.append(f"{int(row['term_months'])} mo")
        secondary = " · ".join(bits)
    else:  # Lease
        amount = (
            f"<span class='ll-card-amt'>{money(row.get('monthly_payment'))}</span>"
            f"<span class='ll-card-unit'>/mo lease</span>"
        )
        bits = []
        if not _isna(row.get("down_payment")):
            bits.append(f"{money(row.get('down_payment'))} due at signing")
        if not _isna(row.get("term_months")):
            bits.append(f"{int(row['term_months'])} mo")
        if not _isna(row.get("annual_mileage")):
            bits.append(f"{int(row['annual_mileage']) // 1000}k mi/yr")
        secondary = " · ".join(bits)

    html = f"""
    <div class='ll-card'>
      <div class='ll-card-media'>
        <img src='{img}' alt='{title}'/>
        <span class='ll-card-type' style='background:{dt_color}'>{deal_type}</span>
        {fav_html}
      </div>
      <div class='ll-card-body'>
        <div class='ll-card-title'>{title}</div>
        <div class='ll-card-sub'>{subtitle}</div>
        <div class='ll-card-price'>{amount}</div>
        <div class='ll-card-spec'>{secondary}</div>
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
