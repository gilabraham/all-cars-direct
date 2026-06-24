"""Headless-browser PDP extractor.

Coral-Springs-style dealer PDPs render their lease / finance / cash pricing
ladders via JavaScript after page load — empty placeholder ``<div>``s in
the static HTML get populated by XHR calls to internal APIs. Plain
``requests.get`` only sees the empty placeholders.

This module spins up a single headless Chromium (Playwright), visits each
PDP once per deal type (cash → finance → lease), waits for network idle,
then parses the rendered text for pricing.

Heavy: ~3-5s per PDP visit, so 3 visits per VIN = 9-15s. For 95 listings
expect ~15-25 minutes. Requires ``playwright install chromium`` once.
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:    # pragma: no cover
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None  # type: ignore


@contextmanager
def browser_session(headless: bool = True, timeout_ms: int = 30000):
    """Yields a single Chromium context reused across many PDP visits."""
    if not PLAYWRIGHT_AVAILABLE:
        raise RuntimeError(
            "Playwright isn't installed. Run `pip install playwright && "
            "playwright install chromium` first."
        )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        context.set_default_timeout(timeout_ms)
        try:
            yield context
        finally:
            context.close()
            browser.close()


def render_pdp(context, url: str, wait_extra_ms: int = 1500) -> str:
    """Fetch ``url`` in a real browser tab, wait for network idle + a brief
    settle period, return the fully-rendered HTML."""
    page = context.new_page()
    try:
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(wait_extra_ms)
        return page.content()
    finally:
        page.close()


# ---------------------------------------------------------------- parsers
def _money(s) -> float | None:
    if s is None:
        return None
    m = re.search(r"[\d,]+(?:\.\d{1,2})?", str(s).replace(",", ""))
    try:
        return float(m.group()) if m else None
    except (TypeError, ValueError):
        return None


def _int(s) -> int | None:
    v = _money(s)
    return int(v) if v is not None else None


_PAY_PATTERN = re.compile(
    r"\$(?P<mo>[\d,]+(?:\.\d{2})?)\s*Per\s*month.*?"
    r"for\s+(?P<term>\d{1,3})\s*months?.*?"
    r"\$?(?P<down>[\d,]+(?:\.\d{2})?)\s*Down\s*Payment",
    re.IGNORECASE | re.DOTALL,
)


def _payment_box_text(html: str) -> str:
    from bs4 import BeautifulSoup
    box = BeautifulSoup(html, "lxml").find(class_="oem-payment-box")
    return box.get_text(" ", strip=True) if box else ""


def _parse_payment(html: str) -> dict | None:
    """Pull (monthly, term_months, down_payment) from a rendered PDP's
    currently-active payment box. ``None`` if the regex didn't match."""
    text = _payment_box_text(html)
    if not text:
        return None
    m = _PAY_PATTERN.search(text)
    if not m:
        return None
    return {
        "monthly": _money(m.group("mo")),
        "term_months": _int(m.group("term")),
        "down_payment": _money(m.group("down")),
    }


def _parse_msrp_and_photos(html: str) -> dict:
    """MSRP + photo URLs from any rendered PDP (deal-type agnostic)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    out: dict = {}

    for label in ("MSRP", "Manufacturer's Suggested Retail Price"):
        node = soup.find(string=re.compile(rf"\b{re.escape(label)}\b", re.I))
        if not node:
            continue
        nxt = node.find_parent().find_next(string=re.compile(r"\$[\d,]+"))
        if nxt:
            v = _money(str(nxt))
            if v and v > 1000:
                out["msrp"] = v
                break

    photos: list[str] = []
    seen = set()
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if any(h in src.lower() for h in ("cai-media-management", "homenetiol",
                                           "secureoffersites/images/get")):
            if src not in seen:
                seen.add(src)
                photos.append(src)
    if photos:
        out["photos"] = photos[:12]
    return out


def scrape_pdp_all_deal_types(context, base_url: str) -> dict:
    """Visit a Coral-Springs-style PDP once per deal type (cash, finance,
    lease) and merge all pricing variants into a single record.

    ``base_url`` may already have a ``type=...`` param — we strip it and
    re-add each deal type in turn.
    """
    parsed = urlparse(base_url)
    qs = [(k, v) for k, v in parse_qsl(parsed.query) if k.lower() != "type"]

    out: dict = {}
    extras_taken = False

    for deal_type in ("cash", "finance", "lease"):
        qs_with_type = qs + [("type", deal_type)]
        url = urlunparse(parsed._replace(query=urlencode(qs_with_type)))
        try:
            html = render_pdp(context, url)
        except Exception:
            continue

        pay = _parse_payment(html)
        if pay:
            if deal_type == "lease":
                out["lease_monthly"] = pay["monthly"]
                out["lease_term_months"] = pay["term_months"]
                out["lease_down_payment"] = pay["down_payment"]
            elif deal_type == "finance":
                out["finance_monthly"] = pay["monthly"]
                out["finance_term_months"] = pay["term_months"]
                out["finance_down_payment"] = pay["down_payment"]
                # APR if exposed elsewhere in the rendered text
                text = _payment_box_text(html)
                m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*APR", text, re.IGNORECASE)
                if m:
                    try:
                        out["finance_apr"] = float(m.group(1))
                    except ValueError:
                        pass
            # "cash" payment is a financed-equivalent estimate; the true cash
            # price comes from selling_price on the listings page.

        if deal_type == "cash":
            # The cash tab is where the dealer shows the actual cash price,
            # usually labeled "Cash" with a $XX,XXX value.
            text = _payment_box_text(html)
            m = re.search(r"Cash\s*(?:Price)?[\s:]*\$([\d,]+(?:\.\d{2})?)",
                          text, re.IGNORECASE)
            if m:
                v = _money(m.group(1))
                if v and v > 1000:
                    out["cash_price"] = v

        if not extras_taken:
            extra = _parse_msrp_and_photos(html)
            if extra:
                out.update(extra)
                extras_taken = True

    return out
