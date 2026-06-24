"""Crawler runner: fetch a URL, parse it, upsert listings, record the run."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from .. import db
from .parsers import PARSERS
from .parsers.generic import _flatten_jsonld, _money, _node_type, _normalize_body, _pick_image, _VEHICLE_TYPES, _PRODUCT_TYPES

USER_AGENT = "AllCarsDirectBot/1.0 (+https://allcarsdirect.example/bot)"
DEFAULT_TIMEOUT = 15
DEFAULT_MAX_FOLLOW = 25
DEFAULT_DELAY = 1.0     # seconds between requests when following list links
DEFAULT_PDP_DELAY = 0.6 # seconds between detail-page requests (kinder to dealer)


@dataclass
class CrawlResult:
    fetched_pages: int = 0
    new_listings: int = 0
    updated_listings: int = 0
    listings: list[dict] = field(default_factory=list)
    status: str = "ok"
    error: str = ""


def _allowed_by_robots(url: str, ua: str = USER_AGENT) -> bool:
    try:
        parsed = urlparse(url)
        rp = RobotFileParser()
        rp.set_url(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
        rp.read()
        return rp.can_fetch(ua, url)
    except Exception:
        # If robots.txt is unreachable, default to allowed (best-effort).
        return True


def _fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    return resp.text


def _pdp_extras(html: str) -> dict:
    """Return extra fields extractable from a vehicle detail (PDP) page.

    Coral-Springs-style PDPs publish bodyType, interior color, transmission,
    and a different ``offers.price`` (typically MSRP, before manufacturer
    rebate) in their JSON-LD. We only fill in what the listings-page parser
    missed — never overwrite a value already set.

    Many dealer PDPs render MSRP/savings/multiple photos via JavaScript,
    which we don't see in the static HTML fetch. Headless-browser scrape
    would be required to capture those.
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    node = None
    for n in _flatten_jsonld(soup):
        if _node_type(n) & (_VEHICLE_TYPES | _PRODUCT_TYPES):
            node = n
            break
    if not node:
        return {}

    offers = node.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}

    extras: dict = {}

    # Body type — PDPs often have this where the listings page doesn't.
    body = _normalize_body(node.get("bodyType") or "")
    if body:
        extras["body_type"] = body

    # Interior color, transmission — useful spec details.
    if node.get("vehicleInteriorColor"):
        extras["interior_color"] = node["vehicleInteriorColor"].strip()
    if node.get("vehicleTransmission"):
        extras["transmission"] = node["vehicleTransmission"].strip()

    # Exterior color (in case the listings page missed it).
    if node.get("color"):
        extras["exterior_color"] = node["color"].strip()

    # PDP offers.price is typically MSRP (before discounts); listings price
    # is post-rebate selling price. If they differ, treat the higher as MSRP.
    pdp_price = _money(offers.get("price")) if isinstance(offers, dict) else None
    if pdp_price:
        extras["_pdp_price"] = pdp_price

    # Image (when the listings page provided a thin stock render, PDP may
    # have a better one).
    img = _pick_image(node.get("image") or node.get("photo"))
    if img:
        extras["_pdp_image"] = img

    # Longer description if present.
    desc = (node.get("description") or "")
    if desc and len(desc) > 20:
        extras["description"] = desc[:600]

    return extras


def _merge_pdp_into_listing(listing: dict, extras: dict) -> None:
    """Fill blanks in ``listing`` from PDP ``extras`` (no overwrite, except
    that a larger PDP price is treated as MSRP if listing had none)."""
    for k in ("body_type", "interior_color", "transmission", "exterior_color"):
        if extras.get(k) and not listing.get(k):
            listing[k] = extras[k]
    # Description: PDPs sometimes have a richer one — only swap if listing's
    # is shorter.
    pdp_desc = extras.get("description")
    if pdp_desc and len(pdp_desc) > len(listing.get("description") or ""):
        listing["description"] = pdp_desc
    # MSRP: if PDP price is higher than the listing's selling price, treat
    # the PDP value as MSRP (the "before incentive" sticker price).
    pdp_price = extras.get("_pdp_price")
    sell = listing.get("selling_price")
    if pdp_price and sell and pdp_price > sell and not listing.get("msrp"):
        listing["msrp"] = pdp_price
    # Prefer the PDP image — it's usually a real dealer-uploaded photo,
    # while the listings page tends to use the generic EvoxImage stock render.
    if extras.get("_pdp_image"):
        listing["image_url"] = extras["_pdp_image"]


def crawl_url(url: str, parser_kind: str = "generic",
              config: dict | str | None = None,
              max_follow: int = DEFAULT_MAX_FOLLOW,
              respect_robots: bool = True,
              deep: bool = True,
              headless: bool = False) -> tuple[list[dict], int]:
    """Fetch ``url`` with the named parser and return (listings, pages_fetched).

    - If the parser returns ``{_follow_url: ...}`` markers (list-page mode),
      each follow URL is fetched with the same parser, up to ``max_follow``.
    - If ``deep=True`` (default), each parsed listing's ``detail_url`` is
      ALSO fetched and merged in for fields the listings page didn't expose
      (interior color, transmission, MSRP, etc.). Adds ~0.6s per listing.
    """
    if respect_robots and not _allowed_by_robots(url):
        raise PermissionError(f"robots.txt disallows fetching {url}")

    parser_cls = PARSERS.get(parser_kind, PARSERS["generic"])
    parser = parser_cls.from_config(config)

    html = _fetch(url)
    pages_fetched = 1
    raw = list(parser.parse(html, url))

    listings: list[dict] = []
    follow_urls: list[str] = []
    for item in raw:
        if "_follow_url" in item:
            follow_urls.append(item["_follow_url"])
        else:
            listings.append(item)

    for follow in follow_urls[:max_follow]:
        try:
            if respect_robots and not _allowed_by_robots(follow):
                continue
            html2 = _fetch(follow)
            pages_fetched += 1
            for row in parser.parse(html2, follow):
                if "_follow_url" not in row:
                    listings.append(row)
            time.sleep(DEFAULT_DELAY)
        except Exception:
            # Skip one bad detail page; keep going.
            continue

    if deep and not headless:
        for listing in listings:
            durl = listing.pop("detail_url", None)
            if not durl:
                continue
            try:
                if respect_robots and not _allowed_by_robots(durl):
                    continue
                pdp_html = _fetch(durl)
                pages_fetched += 1
                _merge_pdp_into_listing(listing, _pdp_extras(pdp_html))
                time.sleep(DEFAULT_PDP_DELAY)
            except Exception:
                # One slow / dead PDP shouldn't kill the whole crawl.
                continue

    if headless:
        # Headless Chromium: 3 visits per VIN (cash / finance / lease) so we
        # capture each deal type's pricing block. ~10-15s per VIN.
        from .headless import browser_session, scrape_pdp_all_deal_types, render_pdp
        import json as _json
        with browser_session() as ctx:
            for listing in listings:
                durl = listing.pop("detail_url", None)
                if not durl:
                    continue
                try:
                    if respect_robots and not _allowed_by_robots(durl):
                        continue
                    extras = scrape_pdp_all_deal_types(ctx, durl)
                    pages_fetched += 3   # cash + finance + lease visits
                    # First, also pull static JSON-LD goodies from one render
                    if extras:
                        # Re-render once to get the static parser's extras too
                        # (interior_color, transmission, bodyType, image)
                        try:
                            html_static = render_pdp(ctx, durl)
                            _merge_pdp_into_listing(listing, _pdp_extras(html_static))
                        except Exception:
                            pass
                    photos = extras.pop("photos", None)
                    for k, v in extras.items():
                        if v is not None and not listing.get(k):
                            listing[k] = v
                    if photos:
                        listing["photos_json"] = _json.dumps(photos)
                except Exception:
                    continue

    return listings, pages_fetched


def crawl_source(source_id: int,
                 respect_robots: bool = True,
                 max_follow: int = DEFAULT_MAX_FOLLOW,
                 headless: bool = False) -> CrawlResult:
    """Run the configured crawler for ``source_id`` and persist results.

    ``headless=True`` switches the PDP deep-crawl from plain HTTP to a real
    headless browser, which captures JavaScript-rendered pricing
    (lease / finance / cash ladders, MSRP, multiple photos). 3-5x slower.
    """
    source = db.get_crawl_source(source_id)
    if not source:
        return CrawlResult(status="error", error=f"source {source_id} not found")

    result = CrawlResult()
    run_id: Optional[int] = None
    try:
        listings, pages = crawl_url(
            source["url"],
            parser_kind=source.get("parser_kind") or "generic",
            config=source.get("config"),
            max_follow=max_follow,
            respect_robots=respect_robots,
            headless=headless,
        )
        result.fetched_pages = pages
        result.listings = listings
        # Admin-supplied location + dealer name on the source act as the
        # canonical values for every listing it produces — dealer pages rarely
        # expose useful per-listing seller info, and admins typically know
        # which physical lot a URL maps to. Falls back to whatever the parser
        # found if these are left blank.
        source_location = (source.get("location") or "").strip()
        source_dealer = (source.get("dealer_name") or "").strip()
        for row in listings:
            ext = str(row.pop("external_id", source["url"]))
            if source_location:
                row["location"] = source_location
            if source_dealer:
                row["dealer_name"] = source_dealer
            outcome = db.upsert_crawled_listing(source_id, ext, row)
            if outcome == "inserted":
                result.new_listings += 1
            elif outcome == "updated":
                result.updated_listings += 1
    except Exception as exc:  # noqa: BLE001
        result.status = "error"
        result.error = str(exc)[:500]

    # Persist the run summary on the source + crawl_runs.
    finished = db._now()
    db.insert_crawl_run({
        "source_id": source_id,
        "started_at": finished,           # close enough for single-call runs
        "finished_at": finished,
        "fetched_pages": result.fetched_pages,
        "new_listings": result.new_listings,
        "updated_listings": result.updated_listings,
        "status": result.status,
        "error_message": result.error,
    })
    summary = (
        f"OK — {result.new_listings} new, {result.updated_listings} updated"
        if result.status == "ok" else f"Error — {result.error[:120]}"
    )
    db.update_crawl_source(source_id, {
        "last_run_at": finished,
        "last_status": summary,
    })
    return result
