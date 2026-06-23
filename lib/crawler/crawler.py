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

USER_AGENT = "AllCarsDirectBot/1.0 (+https://allcarsdirect.example/bot)"
DEFAULT_TIMEOUT = 15
DEFAULT_MAX_FOLLOW = 25
DEFAULT_DELAY = 1.0  # seconds between requests when following list links


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


def crawl_url(url: str, parser_kind: str = "generic",
              config: dict | str | None = None,
              max_follow: int = DEFAULT_MAX_FOLLOW,
              respect_robots: bool = True) -> tuple[list[dict], int]:
    """Fetch ``url`` with the named parser and return (listings, pages_fetched).

    If the parser returns ``{_follow_url: ...}`` markers (list-page mode), each
    follow URL is fetched with the same parser, up to ``max_follow``.
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
    return listings, pages_fetched


def crawl_source(source_id: int,
                 respect_robots: bool = True,
                 max_follow: int = DEFAULT_MAX_FOLLOW) -> CrawlResult:
    """Run the configured crawler for ``source_id`` and persist results."""
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
        )
        result.fetched_pages = pages
        result.listings = listings
        # Admin-supplied location on the source acts as the canonical address
        # for every listing it produces — dealer pages rarely expose useful
        # per-listing locations, and admins typically know which physical lot
        # a URL maps to. Falls back to whatever the parser found.
        source_location = (source.get("location") or "").strip()
        for row in listings:
            ext = str(row.pop("external_id", source["url"]))
            if source_location:
                row["location"] = source_location
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
