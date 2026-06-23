"""User-supplied CSS-selector parser.

Config schema::

    {
      "title": "h1.listing-title",
      "price": ".price-amount",
      "image": "img.main-photo@src",
      "make":  ".make",
      "model": ".model",
      "year":  ".year",
      "body_type": ".body",
      "fuel_type": ".fuel",
      "description": ".description",
      "list_links": "a.car-card"     # optional: list-page mode
    }

A selector of the form ``selector@attr`` extracts the named attribute (handy
for images and links). Otherwise the element's text is used.

If ``list_links`` is provided, the parser interprets the URL as a list page
and emits one listing per detail-link found. Otherwise it parses a single
listing from the URL.
"""
from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Parser


def _select(soup: BeautifulSoup, sel: str) -> str:
    """Run a CSS selector, optionally returning an attribute via ``sel@attr``."""
    if not sel:
        return ""
    attr: str | None = None
    if "@" in sel:
        sel, attr = sel.rsplit("@", 1)
    el = soup.select_one(sel)
    if not el:
        return ""
    if attr:
        return (el.get(attr) or "").strip()
    return el.get_text(strip=True)


def _money(x) -> float | None:
    if not x:
        return None
    m = re.search(r"[\d,]+(?:\.\d+)?", str(x).replace(",", ""))
    try:
        return float(m.group()) if m else None
    except (TypeError, ValueError):
        return None


def _int(x) -> int | None:
    v = _money(x)
    return int(v) if v is not None else None


class SelectorParser(Parser):
    """Parses one listing from a URL using admin-supplied CSS selectors."""

    def _parse_one(self, soup: BeautifulSoup, url: str) -> dict | None:
        cfg = self.config
        title = _select(soup, cfg.get("title", ""))
        # Try to pull year/make/model out of the title if individual selectors
        # aren't given.
        year = _int(_select(soup, cfg.get("year", "")))
        make = _select(soup, cfg.get("make", ""))
        model = _select(soup, cfg.get("model", ""))
        if (not year or not make or not model) and title:
            m = re.match(r"\s*(?:(\d{4})\s+)?([A-Za-z][\w-]+)\s+([A-Za-z0-9][\w/.-]*)", title)
            if m:
                if not year and m.group(1):
                    year = int(m.group(1))
                if not make:
                    make = m.group(2)
                if not model:
                    model = m.group(3)
        if not (make and model):
            return None
        return {
            "external_id": url,
            "make": (make or "").strip(),
            "model": (model or "").strip(),
            "year": year,
            "body_type": _select(soup, cfg.get("body_type", "")) or None,
            "fuel_type": _select(soup, cfg.get("fuel_type", "")) or None,
            "deal_type": cfg.get("deal_type") or "Cash",
            "selling_price": _money(_select(soup, cfg.get("price", ""))),
            "msrp": _money(_select(soup, cfg.get("msrp", ""))),
            "annual_mileage": _int(_select(soup, cfg.get("mileage", ""))),
            "image_url": _select(soup, cfg.get("image", "")),
            "description": _select(soup, cfg.get("description", ""))[:600],
            "location": _select(soup, cfg.get("location", "")),
            "dealer_name": _select(soup, cfg.get("dealer", "")),
        }

    def parse(self, html: str, url: str) -> Iterable[dict]:
        soup = BeautifulSoup(html, "lxml")
        list_sel = self.config.get("list_links")
        if not list_sel:
            row = self._parse_one(soup, url)
            return [row] if row else []
        # List-page mode is implemented by the runner (it follows the links
        # and parses each detail page with this same parser). For one-call
        # parse() we just emit the URLs as marker dicts; the runner detects
        # and follows.
        out = []
        for a in soup.select(list_sel):
            href = a.get("href")
            if not href:
                continue
            out.append({"_follow_url": urljoin(url, href)})
        return out
