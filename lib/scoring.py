"""Deal metrics & scoring, inspired by lease-shopping heuristics.

The "1% rule" is a common lease yardstick: a strong lease has an effective
monthly cost at or below ~1% of MSRP. We surface that plus a 0-100 deal score
and a human-friendly rating badge.
"""
from __future__ import annotations

import math

import pandas as pd


def _num(x) -> float | None:
    if x is None:
        return None
    try:
        if isinstance(x, float) and math.isnan(x):
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def effective_monthly(monthly, down, term) -> float | None:
    """Monthly cost with any due-at-signing amount amortised over the term."""
    m = _num(monthly)
    if m is None:
        return None
    d = _num(down) or 0.0
    t = _num(term)
    if not t or t <= 0:
        return m
    return m + d / t


def percent_of_msrp(monthly, down, term, msrp) -> float | None:
    """Effective monthly as a percentage of MSRP (the '1% rule' metric)."""
    eff = effective_monthly(monthly, down, term)
    s = _num(msrp)
    if eff is None or not s or s <= 0:
        return None
    return eff / s * 100.0


def discount_percent(selling_price, msrp) -> float | None:
    sp = _num(selling_price)
    s = _num(msrp)
    if sp is None or not s or s <= 0:
        return None
    return (s - sp) / s * 100.0


def deal_score(monthly, down, term, msrp) -> int | None:
    """0-100 score; higher is a better value. Centred on the 1% rule."""
    pct = percent_of_msrp(monthly, down, term, msrp)
    if pct is None:
        return None
    # pct 0.7 -> ~100, 1.0 -> ~85, 1.5 -> ~60, 2.0 -> ~35
    score = 100 - (pct - 0.7) * 50
    return int(max(0, min(100, round(score))))


def rating(monthly, down, term, msrp) -> tuple[str, str]:
    """Return (label, hex_color) describing the deal quality."""
    pct = percent_of_msrp(monthly, down, term, msrp)
    if pct is None:
        return ("Unrated", "#94a3b8")
    if pct <= 0.8:
        return ("Unicorn", "#7c3aed")
    if pct <= 1.0:
        return ("Great", "#16a34a")
    if pct <= 1.2:
        return ("Good", "#0ea5e9")
    if pct <= 1.5:
        return ("Fair", "#f59e0b")
    return ("Market", "#ef4444")


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Add computed metric columns to a listings DataFrame."""
    if df.empty:
        for col in ["effective_monthly", "percent_of_msrp", "discount_percent", "deal_score"]:
            df[col] = pd.Series(dtype="float")
        df["rating"] = pd.Series(dtype="object")
        return df
    df = df.copy()
    df["effective_monthly"] = df.apply(
        lambda r: effective_monthly(r.get("monthly_payment"), r.get("down_payment"), r.get("term_months")),
        axis=1,
    )
    df["percent_of_msrp"] = df.apply(
        lambda r: percent_of_msrp(
            r.get("monthly_payment"), r.get("down_payment"), r.get("term_months"), r.get("msrp")
        ),
        axis=1,
    )
    df["discount_percent"] = df.apply(
        lambda r: discount_percent(r.get("selling_price"), r.get("msrp")), axis=1
    )
    df["deal_score"] = df.apply(
        lambda r: deal_score(
            r.get("monthly_payment"), r.get("down_payment"), r.get("term_months"), r.get("msrp")
        ),
        axis=1,
    )
    df["rating"] = df.apply(
        lambda r: rating(
            r.get("monthly_payment"), r.get("down_payment"), r.get("term_months"), r.get("msrp")
        )[0],
        axis=1,
    )
    return df
