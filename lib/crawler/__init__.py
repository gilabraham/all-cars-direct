"""Pluggable web-crawler ingest for car listings.

Each admin-configured URL is one ``crawl_sources`` row. The runner fetches
the URL, hands the HTML to a parser, normalises the result into the canonical
listing schema, then upserts via ``db.upsert_crawled_listing``.

Parsers live in ``lib.crawler.parsers``; add a new one by subclassing
``Parser`` and registering it in ``PARSERS``.
"""
from __future__ import annotations

from .crawler import crawl_source, crawl_url
from .parsers import PARSERS, Parser

__all__ = ["crawl_source", "crawl_url", "PARSERS", "Parser"]
