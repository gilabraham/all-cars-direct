"""Listing images: real studio car renders from imagin.studio, with an
offline SVG placeholder as a fallback when make/model is unknown."""
from __future__ import annotations

import base64
import hashlib
import io
from urllib.parse import quote_plus

# imagin.studio "img" is a public demo customer key. It returns a real studio
# render for a given make / modelFamily / year (and a generic car if unmatched).
_IMAGIN = "https://cdn.imagin.studio/getimage"

# Map trim-style model names to the imagin "modelFamily" slug they belong to.
_FAMILY_OVERRIDES = {
    ("BMW", "330i"): "3-series",
    ("Mercedes-Benz", "C300"): "c-class",
    ("Mercedes-Benz", "GLC 300"): "glc",
    ("Lexus", "RX 350"): "rx",
    ("Lexus", "ES 350"): "es",
    ("Tesla", "Model 3"): "model3",
    ("Tesla", "Model Y"): "model-y",
    ("Hyundai", "IONIQ 5"): "ioniq-5",
    ("Ford", "Mustang Mach-E"): "mustang-mach-e",
    ("Chevrolet", "Silverado 1500"): "silverado",
    ("Chevrolet", "Equinox EV"): "equinox-ev",
    ("Volkswagen", "ID.4"): "id.4",
    ("Jeep", "Grand Cherokee"): "grand-cherokee",
    ("Mazda", "Mazda3"): "mazda3",
}


def _family(make: str, model: str) -> str:
    key = ((make or "").strip(), (model or "").strip())
    if key in _FAMILY_OVERRIDES:
        return _FAMILY_OVERRIDES[key]
    return (model or "").strip().lower().replace(" ", "-")


def car_photo_url(make: str, model: str, year=None, angle: str = "23") -> str:
    """Build an imagin.studio render URL for a make/model/year."""
    params = [
        "customer=img",
        f"make={quote_plus((make or '').strip().lower())}",
        f"modelFamily={quote_plus(_family(make, model))}",
        f"angle={angle}",
    ]
    if year:
        try:
            params.append(f"modelYear={int(year)}")
        except (TypeError, ValueError):
            pass
    return f"{_IMAGIN}?{'&'.join(params)}"

# Pleasant gradient pairs keyed by hash so each make gets a stable colour.
_GRADIENTS = [
    ("#6366f1", "#8b5cf6"),
    ("#0ea5e9", "#22d3ee"),
    ("#10b981", "#34d399"),
    ("#f59e0b", "#f97316"),
    ("#ef4444", "#f43f5e"),
    ("#8b5cf6", "#ec4899"),
    ("#0891b2", "#0ea5e9"),
    ("#475569", "#1e293b"),
    ("#16a34a", "#65a30d"),
    ("#db2777", "#9333ea"),
]

_CAR_PATH = (
    "M40 150 q10 -55 60 -60 l140 0 q40 0 70 35 l70 8 q40 6 40 40 l0 12 "
    "q0 10 -12 10 l-40 0 a26 26 0 0 0 -52 0 l-150 0 a26 26 0 0 0 -52 0 "
    "l-30 0 q-12 0 -12 -12 z"
)


def _gradient_for(key: str) -> tuple[str, str]:
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return _GRADIENTS[h % len(_GRADIENTS)]


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def placeholder_svg(make: str, model: str, year=None) -> str:
    make = (make or "Car").strip()
    model = (model or "").strip()
    c1, c2 = _gradient_for(make)
    title = _escape(f"{make}")
    subtitle = _escape(f"{model}")
    year_txt = _escape(str(int(year))) if year else ""
    gid = "g" + hashlib.md5((make + model).encode()).hexdigest()[:6]
    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='640' height='360' viewBox='0 0 640 360'>
  <defs>
    <linearGradient id='{gid}' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='{c1}'/>
      <stop offset='100%' stop-color='{c2}'/>
    </linearGradient>
  </defs>
  <rect width='640' height='360' fill='url(#{gid})'/>
  <g transform='translate(140 70) scale(0.9)' fill='rgba(255,255,255,0.16)'>
    <path d='{_CAR_PATH}'/>
  </g>
  <text x='40' y='250' font-family='Helvetica, Arial, sans-serif' font-size='42' font-weight='700' fill='#ffffff'>{title}</text>
  <text x='40' y='292' font-family='Helvetica, Arial, sans-serif' font-size='26' fill='rgba(255,255,255,0.92)'>{subtitle}</text>
  <text x='600' y='60' text-anchor='end' font-family='Helvetica, Arial, sans-serif' font-size='28' font-weight='700' fill='rgba(255,255,255,0.85)'>{year_txt}</text>
</svg>"""


def to_data_uri(file, max_width: int = 900, quality: int = 82) -> str:
    """Compress an uploaded image file into a JPEG data URI for storage in image_url."""
    from PIL import Image

    img = Image.open(file)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    if img.width > max_width:
        new_h = int(img.height * max_width / img.width)
        img = img.resize((max_width, new_h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def image_src(make: str, model: str, year=None, image_url: str | None = None) -> str:
    """Return an <img>-ready src.

    Priority: an explicit image_url, then a real imagin.studio render built from
    make/model/year, then an offline SVG placeholder if make/model is missing.
    """
    if image_url and str(image_url).strip().lower().startswith(("http://", "https://", "data:")):
        return str(image_url).strip()
    if (make or "").strip() and (model or "").strip():
        return car_photo_url(make, model, year)
    svg = placeholder_svg(make, model, year)
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"
