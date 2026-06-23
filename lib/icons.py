"""Inline SVG icons (from Lucide, https://lucide.dev — ISC licensed) for use
inside custom HTML (hero banners, deal cards).

Streamlit's `:material/name:` markdown syntax does not render inside raw HTML
blocks, so for those we embed self-contained Lucide SVGs (no external load).
Lucide icons are stroke-based on a 24x24 grid.
"""
from __future__ import annotations

import base64
import functools
import re
from pathlib import Path

# Inner SVG markup for each Lucide icon (everything inside <svg>…</svg>).
_ICONS = {
    "car": (
        "<path d='M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3"
        "c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2'/>"
        "<circle cx='7' cy='17' r='2'/><path d='M9 17h6'/><circle cx='17' cy='17' r='2'/>"
    ),
    "arrow-left-right": (
        "<path d='M8 3 4 7l4 4'/><path d='M4 7h16'/><path d='m16 21 4-4-4-4'/><path d='M20 17H4'/>"
    ),
    "layout-dashboard": (
        "<rect width='7' height='9' x='3' y='3' rx='1'/><rect width='7' height='5' x='14' y='3' rx='1'/>"
        "<rect width='7' height='9' x='14' y='12' rx='1'/><rect width='7' height='5' x='3' y='16' rx='1'/>"
    ),
    "wrench": (
        "<path d='M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94"
        "l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z'/>"
    ),
    "upload": (
        "<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/>"
        "<polyline points='17 8 12 3 7 8'/><line x1='12' x2='12' y1='3' y2='15'/>"
    ),
    "map-pin": (
        "<path d='M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z'/><circle cx='12' cy='10' r='3'/>"
    ),
    "star": (
        "<polygon points='12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 "
        "2 9.27 8.91 8.26 12 2'/>"
    ),
    "route": (
        "<circle cx='6' cy='19' r='3'/>"
        "<path d='M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15'/>"
        "<circle cx='18' cy='5' r='3'/>"
    ),
    "info": "<circle cx='12' cy='12' r='10'/><path d='M12 16v-4'/><path d='M12 8h.01'/>",
    "inbox": (
        "<path d='M22 12h-6l-2 3h-4l-2-3H2'/>"
        "<path d='M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24"
        "a2 2 0 0 0-1.79 1.11z'/>"
    ),
    "layers": (
        "<path d='m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0"
        "l8.58-3.9a1 1 0 0 0 0-1.83Z'/>"
        "<path d='M2 12.18a1 1 0 0 0 .6.91l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 .6-.92'/>"
        "<path d='M2 17.18a1 1 0 0 0 .6.91l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 .6-.92'/>"
    ),
    "check-circle": "<path d='M21.801 10A10 10 0 1 1 17 3.335'/><path d='m9 11 3 3L22 4'/>",
    "dollar-sign": (
        "<line x1='12' x2='12' y1='2' y2='22'/>"
        "<path d='M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6'/>"
    ),
    "percent": (
        "<line x1='19' x2='5' y1='5' y2='19'/>"
        "<circle cx='6.5' cy='6.5' r='2.5'/><circle cx='17.5' cy='17.5' r='2.5'/>"
    ),
    "tag": (
        "<path d='M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 "
        "8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z'/><circle cx='7.5' cy='7.5' r='1'/>"
    ),
    "bell": (
        "<path d='M10.268 21a2 2 0 0 0 3.464 0'/>"
        "<path d='M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8"
        "A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326'/>"
    ),
    "phone": (
        "<path d='M13.832 16.568a1 1 0 0 0 1.213-.303l.355-.465A2 2 0 0 1 17 15h3a2 2 0 0 1 2 2v3"
        "a2 2 0 0 1-2 2A18 18 0 0 1 2 4a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v3a2 2 0 0 1-.8 1.6l-.468.351"
        "a1 1 0 0 0-.292 1.233 14 14 0 0 0 6.392 6.384z'/>"
    ),
    "search": (
        "<circle cx='11' cy='11' r='8'/><path d='m21 21-4.3-4.3'/>"
    ),
    "file-text": (
        "<path d='M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z'/>"
        "<path d='M14 2v4a2 2 0 0 0 2 2h4'/>"
        "<path d='M10 9H8'/><path d='M16 13H8'/><path d='M16 17H8'/>"
    ),
    "bolt": (
        "<path d='M13 2 3 14h9l-1 8 10-12h-9l1-8z'/>"
    ),
    "arrow-right": (
        "<path d='M5 12h14'/><path d='m12 5 7 7-7 7'/>"
    ),
    "key": (
        "<path d='M2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4a6.5 6.5 0 1 0-4-4Z'/>"
        "<circle cx='16.5' cy='7.5' r='.5' fill='currentColor'/>"
    ),
}

# Friendly aliases so call sites read clearly.
_ALIASES = {
    "directions_car": "car",
    "compare_arrows": "arrow-left-right",
    "dashboard": "layout-dashboard",
    "build": "wrench",
    "location_on": "map-pin",
}


def icon(name: str, size: int = 16, color: str = "currentColor", fill: str = "none") -> str:
    inner = _ICONS[_ALIASES.get(name, name)]
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' "
        f"viewBox='0 0 24 24' fill='{fill}' stroke='{color}' stroke-width='2' "
        f"stroke-linecap='round' stroke-linejoin='round' "
        f"style='vertical-align:middle;flex-shrink:0'>{inner}</svg>"
    )


# Side-profile silhouettes for each body type. 100×42 viewBox: body + glass
# + wheel-arches + a soft ground shadow. Designed to read clearly at 56–72 px.
_BODY_SHAPES = {
    "SUV": {
        "body":  "M6 30 L14 30 C16 18 22 14 36 14 L66 14 C76 14 84 18 92 22 L96 26 L96 30 L88 30",
        "glass": "M20 23 L26 17 L48 17 L48 23 Z M50 23 L50 17 L62 17 L70 23 Z",
    },
    "Sedan": {
        "body":  "M6 30 L14 30 C14 24 18 22 28 18 L42 14 L60 14 L78 22 L92 26 L96 28 L96 30 L88 30",
        "glass": "M28 22 L34 16 L48 14 L48 22 Z M50 22 L50 14 L60 14 L74 22 Z",
    },
    "Truck": {
        "body":  "M6 30 L14 30 C14 22 20 18 30 16 L42 14 L56 14 L56 28 L96 28 L96 30 L88 30",
        "glass": "M28 22 L34 17 L52 16 L52 22 Z",
    },
    "Coupe": {
        "body":  "M6 30 L14 30 C14 24 18 22 28 19 C40 12 56 12 70 17 L84 22 L94 26 L96 28 L96 30 L88 30",
        "glass": "M30 22 L40 15 L60 14 L74 22 Z",
    },
    "Convertible": {
        "body":  "M6 30 L14 30 C14 22 22 18 36 16 L66 16 C78 18 86 22 92 25 L96 28 L96 30 L88 30",
        "glass": "M30 22 L42 19 L62 19 L70 22 Z",
        "extras": "M58 22 L66 22 L66 16 L58 18 Z",
    },
    "Hatchback": {
        "body":  "M6 30 L14 30 C14 22 18 18 28 16 L46 14 L62 14 L80 20 L88 26 L92 28 L96 28 L96 30 L88 30",
        "glass": "M28 22 L34 17 L48 14 L48 22 Z M50 22 L50 14 L60 14 L76 22 Z",
    },
    "Wagon": {
        "body":  "M6 30 L14 30 C14 22 18 18 28 16 L62 14 L86 16 L92 22 L96 26 L96 30 L88 30",
        "glass": "M28 22 L34 17 L48 16 L48 22 Z M50 22 L50 16 L78 16 L86 22 Z",
    },
    "Minivan": {
        "body":  "M6 30 L14 30 C14 22 18 16 30 14 L78 14 C86 16 90 20 94 24 L96 28 L96 30 L88 30",
        "glass": "M22 22 L28 16 L46 16 L46 22 Z M48 22 L48 16 L66 16 L66 22 Z M68 22 L68 16 L84 16 L88 22 Z",
    },
}
# Aliases for terms the parser may emit.
_BODY_SHAPES["Crossover"] = _BODY_SHAPES["SUV"]
_BODY_SHAPES["Van"] = _BODY_SHAPES["Minivan"]


def _wheel(cx: int, color: str) -> str:
    """One wheel: tire + rim + 4 spokes."""
    return (
        f"<circle cx='{cx}' cy='32' r='6' fill='{color}'/>"
        f"<circle cx='{cx}' cy='32' r='3' fill='#fff'/>"
        f"<circle cx='{cx}' cy='32' r='1.2' fill='{color}'/>"
    )


def body_icon_svg(name: str, size: int = 56, color: str = "#0E2A47") -> str:
    """Return an inline SVG silhouette for a body type.

    Crisp 3D-render-inspired side profile with glass, two wheels, and a soft
    drop shadow. Falls back to the Sedan profile for unknown body types.
    """
    shape = _BODY_SHAPES.get(name, _BODY_SHAPES["Sedan"])
    h = int(size * 0.46)
    body = shape["body"]
    glass = shape.get("glass", "")
    extras = shape.get("extras", "")
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{h}' "
        f"viewBox='0 0 100 42' style='display:block'>"
        # Soft ground shadow
        f"<ellipse cx='52' cy='39' rx='44' ry='1.6' fill='{color}' fill-opacity='0.15'/>"
        # Car body fill
        f"<path d='{body}' fill='{color}'/>"
        # Window glass cutouts
        f"<path d='{glass}' fill='#fff'/>"
        + (f"<path d='{extras}' fill='{color}'/>" if extras else "")
        # Wheels
        + _wheel(22, color)
        + _wheel(80, color)
        + "</svg>"
    )


# ---------------------------------------------------------------- Photo icons
# Per-body-type photo assets live at ``assets/body-types/<slug>.{webp,png}``.
# Preferred format is WebP (smaller, transparent). PNG is accepted as a
# fallback so the temporary slices from scripts/slice_body_sprite.py keep
# working until proper renders are produced.
_BODY_PHOTO_DIR = Path(__file__).resolve().parent.parent / "assets" / "body-types"
_BODY_PHOTO_EXTS = ("webp", "png")  # priority order
# Visual aliases for body types that share a silhouette with one we ship.
# Keep the original filter value (so counts stay accurate) but render the
# closest matching photo.
_BODY_PHOTO_ALIASES = {
    "crossover": "suv",
    "van": "minivan",
    "passenger_van": "minivan",
    "mini_van": "minivan",
    "pickup": "truck",
    "pickup_truck": "truck",
    "sport_utility": "suv",
}

# Recommended source canvas: 300×120 px (2.5:1). The filter rail renders the
# icon at a fixed HEIGHT, with width filling the available column up to a cap
# so the cell never overflows the (narrow) filter rail.
# Default (filter-rail) dimensions. Callers can pass ``size`` to scale up for
# bigger contexts like homepage tiles — height becomes ``size`` and width caps
# at roughly 3× height so wide source aspects don't overflow the container.
_BODY_ICON_H = 28
_BODY_ICON_MAX_W = 80
_BODY_ICON_WIDTH_RATIO = 3.0  # max width relative to height


@functools.lru_cache(maxsize=16)
def _body_photo_data_uri(path_str: str, mtime: float) -> str:
    """Inline a per-body image as a data URI. Cached by (path, mtime)."""
    del mtime
    path = Path(path_str)
    data = path.read_bytes()
    mime = "image/webp" if path.suffix.lower() == ".webp" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def _body_photo_path(name: str) -> Path | None:
    slug = name.lower().replace(" ", "_")
    slug = _BODY_PHOTO_ALIASES.get(slug, slug)
    for ext in _BODY_PHOTO_EXTS:
        p = _BODY_PHOTO_DIR / f"{slug}.{ext}"
        if p.exists():
            return p
    return None


def body_icon_html(name: str, size: int | None = None, color: str = "#0E2A47") -> str:
    """Photo silhouette (if a per-body asset exists) → otherwise SVG fallback.

    The asset is rendered inside a fixed cell so every row in the filter rail
    has identical footprint regardless of source car length. ``size`` is
    kept for the SVG fallback only.
    """
    path = _body_photo_path(name)
    if path is not None:
        # Use ``size`` as the rendered HEIGHT (defaults to filter-rail size).
        # Width caps proportionally so wide source aspects don't blow out the
        # container — object-fit:contain handles the rest.
        h = size if size is not None else _BODY_ICON_H
        max_w = max(_BODY_ICON_MAX_W, int(h * _BODY_ICON_WIDTH_RATIO))
        url = _body_photo_data_uri(str(path), path.stat().st_mtime)
        return (
            f"<div style='width:100%;max-width:{max_w}px;"
            f"height:{h}px;margin-left:auto;"
            f"display:flex;align-items:center;justify-content:flex-end;'>"
            f"<img src='{url}' alt='{name}' "
            f"style='max-width:100%;max-height:100%;object-fit:contain;"
            f"display:block;'/>"
            f"</div>"
        )
    return body_icon_svg(name, size=size or 64, color=color)


def body_sprite_stylesheet(size: int = 32) -> str:
    """Kept for backwards-compat with views that still inject a stylesheet."""
    del size
    return ""


# ---------------------------------------------------------------- Make logos
# Brand mark SVGs from cardog-ai/icons (MIT). Bundled under assets/car-logos/
# with slugified filenames (e.g. "Alfa Romeo Icon.svg" → "alfa-romeo.svg").
_MAKE_LOGO_DIR = Path(__file__).resolve().parent.parent / "assets" / "car-logos"

# Brand-name aliases: maps common DB strings → the slug used in the file name.
_MAKE_ALIASES = {
    "mercedes-benz": "mb",
    "mercedes benz": "mb",
    "mercedes": "mb",
    "land rover": "landrover",
    "range rover": "landrover",
    "alfa": "alfa-romeo",
    "vw": "volkswagen",
    "chevy": "chevrolet",
}


def _make_slug(name: str) -> str:
    key = (name or "").strip().lower()
    if key in _MAKE_ALIASES:
        return _MAKE_ALIASES[key]
    # Default slug: lowercase, spaces & ampersand-style joiners → hyphens.
    slug = key.replace("&", "and")
    slug = "-".join(slug.split())
    return slug


@functools.lru_cache(maxsize=128)
def _make_logo_svg(slug: str, mtime: float) -> str:
    del mtime  # cache-bust only
    path = _MAKE_LOGO_DIR / f"{slug}.svg"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


_SVG_DIM_RE = re.compile(r'\s(width|height)="[^"]*"')


def make_icon_html(name: str, size: int = 24, align: str = "end") -> str:
    """Inline the brand logo for ``name`` sized to ``size`` px square.

    ``align`` controls horizontal placement inside the wrapper:
      - ``"end"`` (default) — right-aligned, suited to the filter rail.
      - ``"center"`` — centered, suited to homepage tiles.

    Returns an empty string when no logo is available (caller can render a
    text-only label instead). The SVG's baked-in ``width``/``height`` (the
    cardog set ships them at 512×512) are stripped so the parent span sizes
    the icon — otherwise it'd render at native resolution.
    """
    slug = _make_slug(name)
    path = _MAKE_LOGO_DIR / f"{slug}.svg"
    if not path.exists():
        return ""
    svg = _make_logo_svg(slug, path.stat().st_mtime)
    svg = _SVG_DIM_RE.sub("", svg, count=2)
    justify = "center" if align == "center" else "flex-end"
    margin_left = "0" if align == "center" else "auto"
    return (
        f"<span style='display:inline-flex;align-items:center;justify-content:{justify};"
        f"width:100%;height:{size}px;margin-left:{margin_left};line-height:0;'>"
        f"<span style='display:inline-block;width:{size}px;height:{size}px;"
        f"flex:0 0 auto;'>{svg}</span>"
        f"</span>"
    )


def logo(size: int = 36, ring1: str = "#6366f1", ring2: str = "#8b5cf6",
         glyph: str = "#ffffff") -> str:
    """Company logo: a gradient circular badge with the car glyph inside."""
    car = _ICONS["car"]
    gid = f"llg{ring1[1:]}{ring2[1:]}"
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' "
        f"viewBox='0 0 40 40' style='vertical-align:middle;flex-shrink:0'>"
        f"<defs><linearGradient id='{gid}' x1='0' y1='0' x2='1' y2='1'>"
        f"<stop offset='0%' stop-color='{ring1}'/><stop offset='100%' stop-color='{ring2}'/>"
        f"</linearGradient></defs>"
        f"<circle cx='20' cy='20' r='19' fill='url(#{gid})'/>"
        f"<g transform='translate(8 8.5)' fill='none' stroke='{glyph}' stroke-width='2' "
        f"stroke-linecap='round' stroke-linejoin='round'>{car}</g></svg>"
    )
