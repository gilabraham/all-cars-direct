"""Generic parser: tries JSON-LD (schema.org/Vehicle, Car, Product) first,
falls back to Open Graph + meta tags, then a few common heuristics.

Works on car-listing pages that publish structured data — many real dealer
sites do, especially those built on Shopify/WordPress/standard e-commerce
stacks. For sites without structured data, configure a SelectorParser instead.
"""
from __future__ import annotations

import html
import json
import re
from typing import Iterable
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from .base import Parser

_VEHICLE_TYPES = {"Vehicle", "Car", "Motorcycle", "BusOrCoach", "MotorizedBicycle"}
_PRODUCT_TYPES = {"Product", "IndividualProduct"}


def _money(x) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x)
    m = re.search(r"[\d,]+(?:\.\d+)?", s.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group())
    except ValueError:
        return None


def _int(x) -> int | None:
    v = _money(x)
    return int(v) if v is not None else None


_BODY_ALIASES = {
    "suv": "SUV", "crossover": "SUV", "sport utility": "SUV",
    "sport-utility": "SUV", "utility": "SUV", "sport utility vehicle": "SUV",
    "sedan": "Sedan", "saloon": "Sedan", "4-door sedan": "Sedan",
    "truck": "Truck", "pickup": "Truck", "pickup truck": "Truck",
    "pickup-truck": "Truck", "crew cab": "Truck", "extended cab": "Truck",
    "coupe": "Coupe", "coupé": "Coupe", "2-door coupe": "Coupe",
    "convertible": "Convertible", "cabriolet": "Convertible", "roadster": "Convertible",
    "hatchback": "Hatchback", "hatch": "Hatchback", "5-door hatchback": "Hatchback",
    "wagon": "Wagon", "estate": "Wagon", "station wagon": "Wagon",
    "minivan": "Minivan", "van": "Minivan", "passenger van": "Minivan",
    "mini-van": "Minivan", "mini van": "Minivan",
}


def _normalize_body(text: str) -> str:
    if not text:
        return ""
    key = re.sub(r"\s+", " ", str(text).strip().lower())
    return _BODY_ALIASES.get(key, str(text).strip().title())


def _body_from_url(url: str) -> str:
    """Pull body type from common URL signals (image params, offer slug)."""
    if not url:
        return ""
    try:
        parsed_url = urlparse(url)
        qs = parse_qs(parsed_url.query)
    except Exception:
        return ""
    for key in ("vehicletype", "bodyType", "body_type", "body"):
        if key in qs and qs[key]:
            return _normalize_body(qs[key][0])
    # Slug tail: try last 3 tokens, then last 2, then last 1 — so
    # "2016-hyundai-tucson-sport-utility" → "sport utility" → "SUV".
    slug = re.split(r"[/?#]", parsed_url.path.lower())[-1]
    tokens = re.split(r"[-_]", slug)
    for n in (3, 2, 1):
        if len(tokens) >= n:
            phrase = " ".join(tokens[-n:])
            if phrase in _BODY_ALIASES:
                return _BODY_ALIASES[phrase]
    return ""


def _pick_image(node) -> str:
    """Schema.org ``image`` can be a string, a list, or an ImageObject dict.

    The dict form uses ``contentUrl`` (canonical) or ``url`` (also accepted).
    JSON-LD values are often HTML-entity-encoded (``&amp;`` → ``&``); unescape.
    """
    while isinstance(node, list):
        node = node[0] if node else None
    if isinstance(node, dict):
        node = node.get("contentUrl") or node.get("url") or ""
    return html.unescape(str(node or "")).strip()


def _flatten_jsonld(soup: BeautifulSoup) -> list[dict]:
    out: list[dict] = []
    for tag in soup.find_all("script", type="application/ld+json"):
        raw = (tag.string or tag.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        stack = [data]
        while stack:
            node = stack.pop()
            if isinstance(node, list):
                stack.extend(node)
            elif isinstance(node, dict):
                out.append(node)
                # also recurse into @graph / mainEntity nested objects
                for v in node.values():
                    if isinstance(v, (list, dict)):
                        stack.append(v)
    return out


def _node_type(node: dict) -> set[str]:
    t = node.get("@type")
    if isinstance(t, list):
        return {str(x) for x in t}
    if isinstance(t, str):
        return {t}
    return set()


def _vehicle_from_jsonld(node: dict, url: str) -> dict | None:
    types = _node_type(node)
    if not (types & (_VEHICLE_TYPES | _PRODUCT_TYPES)):
        return None
    name = node.get("name") or ""
    brand = node.get("brand") or node.get("manufacturer") or ""
    if isinstance(brand, dict):
        brand = brand.get("name") or ""
    model = node.get("model") or ""
    year = node.get("vehicleModelDate") or node.get("modelDate") or node.get("productionDate")
    # Sometimes year is in name like "2025 Toyota RAV4"
    if not year and name:
        m = re.search(r"\b(19|20)\d{2}\b", name)
        if m:
            year = m.group()
    # Make/model fallback from name
    if not brand and name:
        m = re.match(r"^\s*(?:\d{4}\s+)?([A-Za-z][\w-]+)", name)
        if m:
            brand = m.group(1)
    if not model and name and brand:
        rest = re.sub(rf"^\s*\d{{0,4}}\s*{re.escape(str(brand))}\s+", "", name).strip()
        model = rest.split(",")[0].split("-")[0].strip()

    offers = node.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price") if isinstance(offers, dict) else None

    image = _pick_image(node.get("image") or node.get("photo"))

    body = _normalize_body(node.get("bodyType") or "")
    if not body:
        # Fall back to URL signals (image vehicletype param, offer slug).
        offer_url = (offers.get("url") if isinstance(offers, dict) else "") or ""
        body = _body_from_url(image) or _body_from_url(offer_url) or _body_from_url(url)
    if not body:
        # Last-resort: scan name + description for body-type words.
        hay = f"{name} {node.get('description') or ''}".lower()
        for phrase, canonical in _BODY_ALIASES.items():
            if re.search(rf"\b{re.escape(phrase)}\b", hay):
                body = canonical
                break
    fuel = node.get("fuelType") or ""
    miles = node.get("mileageFromOdometer")
    if isinstance(miles, dict):
        miles = miles.get("value")

    return {
        "external_id": str(node.get("@id") or node.get("vehicleIdentificationNumber") or url),
        "make": str(brand).strip() if brand else "",
        "model": str(model).strip() if model else "",
        "year": _int(year),
        "body_type": str(body).strip() or None,
        "fuel_type": str(fuel).strip() or None,
        "deal_type": "Cash",
        "selling_price": _money(price),
        "msrp": _money(node.get("msrp") or node.get("listPrice")),
        "annual_mileage": _int(miles),
        "image_url": image or "",
        "description": (node.get("description") or "")[:600],
        "location": (offers.get("areaServed") if isinstance(offers, dict) else "") or "",
        "dealer_name": (offers.get("seller", {}) or {}).get("name", "") if isinstance(offers, dict) else "",
    }


def _from_open_graph(soup: BeautifulSoup, url: str) -> dict | None:
    def meta(prop):
        tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        return (tag.get("content") if tag else "").strip()

    title = meta("og:title") or (soup.title.get_text().strip() if soup.title else "")
    if not title:
        return None
    image = meta("og:image")
    price = meta("product:price:amount") or meta("og:price:amount")
    description = meta("og:description") or meta("description")

    # Try to pull "YYYY Make Model …" from the title.
    m = re.search(r"\b(19|20)(\d{2})\b\s+([A-Za-z][\w-]+)\s+([A-Za-z0-9][\w/.-]*)", title)
    year = make = model = None
    if m:
        year = int(m.group(1) + m.group(2))
        make, model = m.group(3).strip(), m.group(4).strip()
    return {
        "external_id": url,
        "make": make or "",
        "model": model or "",
        "year": year,
        "selling_price": _money(price),
        "deal_type": "Cash",
        "image_url": image or "",
        "description": (description or "")[:600],
    }


class GenericParser(Parser):
    """Try JSON-LD → Open Graph → minimal heuristics."""

    def parse(self, html: str, url: str) -> Iterable[dict]:
        soup = BeautifulSoup(html, "lxml")
        results: list[dict] = []

        # 1) JSON-LD (yields all Vehicle/Car/Product objects found).
        for node in _flatten_jsonld(soup):
            row = _vehicle_from_jsonld(node, url)
            if row and (row.get("make") or row.get("model")):
                results.append(row)

        if results:
            return results

        # 2) Open Graph + meta fallback (single listing per page).
        og = _from_open_graph(soup, url)
        if og and (og.get("make") or og.get("model")):
            return [og]

        return []
