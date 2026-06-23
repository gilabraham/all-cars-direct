"""Slice ``assets/bodyType.png`` into 8 individual PNGs (one per body type).

The source is a 2×4 grid where individual cars don't share a common baseline
and some extend past their nominal cell — using a fixed grid crop produces
artifacts (cropped tops, neighbor-cell bleed). This script instead detects
each car's actual bounding box and writes a tight, transparent-padded PNG
per body type.

Run after replacing ``assets/bodyType.png``::

    .venv/bin/python scripts/slice_body_sprite.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "bodyType.png"
OUT_DIR = ROOT / "assets" / "body-types"

# Row-major order in the source sprite (matches the user's reference image).
LAYOUT = [
    ["SUV",     "Sedan"],
    ["Truck",   "Coupe"],
    ["Minivan", "Convertible"],
    ["Wagon",   "Hatchback"],
]

# Pixels of transparent padding to add around each detected car (clipped to
# the cell boundary so neighbor content never leaks in).
PAD = 6

# Threshold: pixels lighter than this are treated as background. Strict enough
# to ignore faint row-separator shadow lines (typically gray 210-235) without
# rejecting dark wheel/glass content (typically <100).
WHITE_CUTOFF = 170

# Minimum fraction of cell width that must be non-background in a row/col for
# that row/col to count as "real content" (vs a thin shadow line). Tuned so
# 1-2 px separator lines fall below the bar while wheels / car bodies clear it.
MIN_ROW_DENSITY = 0.06


def _content_bbox(cell: Image.Image) -> tuple[int, int, int, int] | None:
    """Return (x0, y0, x1, y1) of substantial dark content in this cell.

    Uses a two-pass detector:
      1. Find pixels darker than WHITE_CUTOFF (the obvious content).
      2. Trim leading/trailing rows + cols whose density is below
         MIN_ROW_DENSITY — kills thin horizontal shadow lines between cells
         without rejecting wheels that legitimately touch the cell edge.
    """
    W, H = cell.size
    # Source PNG has transparent pixels with RGB(0,0,0). A straight convert("L")
    # would treat the entire "white" background as black. Composite onto white
    # first so brightness reflects what a viewer actually sees.
    rgba = cell.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    gray = Image.alpha_composite(bg, rgba).convert("L")
    data = gray.tobytes()  # row-major bytes, 1 byte per pixel
    row_counts = [
        sum(1 for x in range(W) if data[y * W + x] <= WHITE_CUTOFF)
        for y in range(H)
    ]
    col_counts = [
        sum(1 for y in range(H) if data[y * W + x] <= WHITE_CUTOFF)
        for x in range(W)
    ]
    row_thresh = max(2, int(W * MIN_ROW_DENSITY))
    col_thresh = max(2, int(H * MIN_ROW_DENSITY))

    def _longest_run(counts, thresh, max_gap):
        """Return (start, end_exclusive) of the longest contiguous run of
        rows/cols where count >= thresh. Tolerates internal gaps up to
        ``max_gap`` so legitimate sky-between-roof-and-wheels doesn't split
        the car into pieces.
        """
        best = (0, 0)
        cur_lo = None
        gap = 0
        for i, c in enumerate(counts):
            if c >= thresh:
                if cur_lo is None:
                    cur_lo = i
                gap = 0
            else:
                if cur_lo is not None:
                    gap += 1
                    if gap > max_gap:
                        cur_end = i - gap + 1
                        if cur_end - cur_lo > best[1] - best[0]:
                            best = (cur_lo, cur_end)
                        cur_lo = None
                        gap = 0
        if cur_lo is not None:
            cur_end = len(counts) - gap
            if cur_end - cur_lo > best[1] - best[0]:
                best = (cur_lo, cur_end)
        return best

    # Vertical: allow ~30 px of internal gap (sky between roof and ground line).
    # Horizontal: allow ~50 px (between bumpers/wheels). Anything bigger than
    # those reasonably indicates content from a different cell.
    y0, y1 = _longest_run(row_counts, row_thresh, max_gap=30)
    x0, x1 = _longest_run(col_counts, col_thresh, max_gap=60)
    if y0 >= y1 or x0 >= x1:
        return None
    return (x0, y0, x1, y1)


def _expand_into_neighbors(img: Image.Image, base_box: tuple[int, int, int, int],
                            r: int, c: int, cw: int, ch: int) -> Image.Image:
    """Crop content from the source. Padding stays within column horizontally,
    but allows a small spill into neighbor cells vertically (cars sometimes
    do — e.g. truck wheels extend slightly past the cell bottom).
    """
    W, H = img.size
    x0, y0, x1, y1 = base_box
    # Horizontal: pad + clip to cell column.
    x0 = max(0, x0 - PAD)
    x1 = min(cw, x1 + PAD)
    # Vertical: pad and clip only to the SOURCE image bounds (allowing
    # the box to dip into the neighbor cell above/below by up to PAD).
    gy0 = max(0, r * ch + y0 - PAD)
    gy1 = min(H, r * ch + y1 + PAD)
    return img.crop((c * cw + x0, gy0, c * cw + x1, gy1))


def _to_transparent(cell: Image.Image) -> Image.Image:
    """Knock out the pure-white background to make a transparent PNG."""
    cell = cell.convert("RGBA")
    px = cell.load()
    W, H = cell.size
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            # Treat near-white as transparent (smooth alpha for the very edge).
            m = max(r, g, b)
            if m >= 248:
                px[x, y] = (255, 255, 255, 0)
            elif m >= 230:
                # soft falloff so anti-aliased edges stay clean
                px[x, y] = (r, g, b, int((255 - m) * 11))
    return cell


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"Source sprite not found: {SRC}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    img = Image.open(SRC)
    W, H = img.size
    cols, rows = 2, 4
    cw, ch = W // cols, H // rows
    print(f"Source: {SRC.name} ({W}×{H}), nominal cell {cw}×{ch}")

    # Cars in this source sometimes spill across the nominal cell boundary
    # (truck wheels poke into the cell below). Crop a slightly oversized
    # window per cell so the bbox detector can capture the full car, then
    # the run-trimming inside _content_bbox discards content that belongs
    # to neighbor cars.
    OVERLAP = 20
    for r in range(rows):
        for c in range(cols):
            name = LAYOUT[r][c]
            # Expanded window: extend ±OVERLAP vertically (cars are arranged
            # in rows so vertical spill is the only realistic case), clipped
            # to the source image bounds.
            y_lo = max(0, r * ch - OVERLAP)
            y_hi = min(H, (r + 1) * ch + OVERLAP)
            window = img.crop((c * cw, y_lo, (c + 1) * cw, y_hi))
            bbox = _content_bbox(window)
            if not bbox:
                print(f"  [{name}] EMPTY — skipped")
                continue
            # Translate bbox back to nominal-cell coords (negative y0 = car
            # starts above the nominal cell top) and feed to the existing
            # expander which clips to the nominal cell + PAD.
            x0, y0, x1, y1 = bbox
            offset = y_lo - r * ch  # negative when we extended upward
            bbox_cell = (x0, y0 + offset, x1, y1 + offset)
            cropped = _expand_into_neighbors(img, bbox_cell, r, c, cw, ch)
            tp = _to_transparent(cropped)
            out = OUT_DIR / f"{name.lower().replace(' ', '_')}.png"
            tp.save(out, optimize=True)
            print(f"  [{name:12s}] -> {out.relative_to(ROOT)} ({tp.size[0]}×{tp.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
