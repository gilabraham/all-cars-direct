"""SQLite data layer for All Cars Direct listings."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Default to a project-local data dir for dev; let deploys override via the
# ACD_DATA_DIR env var (Fly mounts a persistent volume at /data).
DATA_DIR = Path(
    os.environ.get("ACD_DATA_DIR")
    or Path(__file__).resolve().parent.parent / "data"
)
DB_PATH = DATA_DIR / "deals.db"

# Canonical column order for listings (excludes id / timestamps).
EDITABLE_COLUMNS = [
    "make",
    "model",
    "year",
    "trim",
    "body_type",
    "deal_type",
    "fuel_type",
    "monthly_payment",
    "down_payment",
    "term_months",
    "annual_mileage",
    "msrp",
    "selling_price",
    "money_factor",
    "residual_percent",
    "exterior_color",
    "interior_color",
    "transmission",
    # Per-deal-type pricing (when the dealer publishes multiple offers per VIN).
    "cash_price",
    "lease_monthly",
    "lease_term_months",
    "lease_down_payment",
    "finance_monthly",
    "finance_term_months",
    "finance_down_payment",
    "finance_apr",
    "photos_json",
    "location",
    "dealer_name",
    "condition",
    "image_url",
    "description",
    "featured",
    "status",
]

NUMERIC_COLUMNS = {
    "year": int,
    "monthly_payment": float,
    "down_payment": float,
    "term_months": int,
    "annual_mileage": int,
    "msrp": float,
    "selling_price": float,
    "money_factor": float,
    "residual_percent": float,
    "featured": int,
    # Per-deal-type pricing (headless PDP scrape).
    "cash_price": float,
    "lease_monthly": float,
    "lease_term_months": int,
    "lease_down_payment": float,
    "finance_monthly": float,
    "finance_term_months": int,
    "finance_down_payment": float,
    "finance_apr": float,
}

DEAL_TYPES = ["Lease", "Finance", "Cash"]
CONDITIONS = ["New", "Pre-Owned"]
BODY_TYPES = [
    "Sedan",
    "SUV",
    "Truck",
    "Coupe",
    "Hatchback",
    "Convertible",
    "Wagon",
    "Minivan",
    "Crossover",
]
FUEL_TYPES = ["Gas", "Hybrid", "Plug-in Hybrid", "Electric", "Diesel"]
STATUSES = ["active", "inactive", "sold"]
INQUIRY_STATUSES = ["New", "Contacted", "Closed"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    trim TEXT,
    body_type TEXT,
    deal_type TEXT NOT NULL DEFAULT 'Lease',
    fuel_type TEXT,
    monthly_payment REAL,
    down_payment REAL DEFAULT 0,
    term_months INTEGER,
    annual_mileage INTEGER,
    msrp REAL,
    selling_price REAL,
    money_factor REAL,
    residual_percent REAL,
    exterior_color TEXT,
    location TEXT,
    dealer_name TEXT,
    image_url TEXT,
    description TEXT,
    featured INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER,
    listing_label TEXT,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    customer_phone TEXT,
    message TEXT,
    status TEXT DEFAULT 'New',
    admin_notes TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS crawl_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    parser_kind TEXT NOT NULL DEFAULT 'generic',
    config TEXT,
    enabled INTEGER DEFAULT 1,
    location TEXT,
    last_run_at TEXT,
    last_status TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS crawl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,
    started_at TEXT,
    finished_at TEXT,
    fetched_pages INTEGER DEFAULT 0,
    new_listings INTEGER DEFAULT 0,
    updated_listings INTEGER DEFAULT 0,
    status TEXT,
    error_message TEXT
);
"""

# Columns added to `listings` via lightweight migrations on init.
_LISTINGS_ADDITIONS = [
    ("crawl_source_id", "INTEGER"),
    ("external_id", "TEXT"),
    ("last_seen_at", "TEXT"),
    ("interior_color", "TEXT"),
    ("transmission", "TEXT"),
    # Per-deal-type pricing captured from headless PDP scrape. The legacy
    # `monthly_payment` / `term_months` / `down_payment` columns hold the
    # *primary* deal type's numbers (whatever ``deal_type`` is set to); these
    # additional columns hold the same fields for the other two types so we
    # can show Cash + Lease + Finance side by side in the detail modal.
    ("lease_monthly", "REAL"),
    ("lease_term_months", "INTEGER"),
    ("lease_down_payment", "REAL"),
    ("finance_monthly", "REAL"),
    ("finance_term_months", "INTEGER"),
    ("finance_down_payment", "REAL"),
    ("finance_apr", "REAL"),
    ("cash_price", "REAL"),
    ("photos_json", "TEXT"),     # JSON list of additional dealer photos
    ("condition", "TEXT"),       # "New" or "Pre-Owned"
]
# Columns added to `crawl_sources` via lightweight migrations on init.
_SOURCES_ADDITIONS = [
    ("location", "TEXT"),
    ("dealer_name", "TEXT"),
]
CRAWLER_PARSER_KINDS = ["generic", "json_ld", "selectors"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def get_conn():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # Lightweight migrations: add new columns to existing tables.
        cols = {r[1] for r in conn.execute("PRAGMA table_info(listings)").fetchall()}
        for col, decl in _LISTINGS_ADDITIONS:
            if col not in cols:
                conn.execute(f"ALTER TABLE listings ADD COLUMN {col} {decl}")
        src_cols = {r[1] for r in conn.execute("PRAGMA table_info(crawl_sources)").fetchall()}
        for col, decl in _SOURCES_ADDITIONS:
            if col not in src_cols:
                conn.execute(f"ALTER TABLE crawl_sources ADD COLUMN {col} {decl}")
        # Backfill ``condition`` for legacy crawled rows. Coral-Springs-style
        # descriptions reliably start with "New " or "Used "; the crawl-source
        # URL also tells us (``/inventory/used`` vs ``/inventory/new``). Only
        # touches rows where ``condition`` is still NULL so manual edits stick.
        conn.execute(
            "UPDATE listings SET condition = 'Pre-Owned' "
            "WHERE condition IS NULL AND ("
            "  description LIKE 'Used %' OR description LIKE 'Pre-Owned%' OR "
            "  crawl_source_id IN ("
            "    SELECT id FROM crawl_sources "
            "    WHERE LOWER(url) LIKE '%/used%' OR LOWER(url) LIKE '%/pre-owned%'"
            "  )"
            ")"
        )
        conn.execute(
            "UPDATE listings SET condition = 'New' "
            "WHERE condition IS NULL AND ("
            "  description LIKE 'New %' OR "
            "  crawl_source_id IN ("
            "    SELECT id FROM crawl_sources "
            "    WHERE LOWER(url) LIKE '%/new%'"
            "  )"
            ")"
        )


def count_listings() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]


def _clean_record(record: dict) -> dict:
    """Coerce a raw record into the column types the DB expects."""
    out: dict = {}
    for col in EDITABLE_COLUMNS:
        val = record.get(col, None)
        if val is None or (isinstance(val, float) and pd.isna(val)):
            out[col] = None
            continue
        if isinstance(val, str) and val.strip() == "":
            out[col] = None
            continue
        caster = NUMERIC_COLUMNS.get(col)
        if caster is not None:
            try:
                out[col] = caster(float(val)) if caster is int else caster(val)
            except (TypeError, ValueError):
                out[col] = None
        else:
            out[col] = str(val).strip()
    # Defaults / normalisation.
    out["deal_type"] = out.get("deal_type") or "Lease"
    out["status"] = (out.get("status") or "active").lower()
    out["featured"] = int(out.get("featured") or 0)
    if out.get("down_payment") is None:
        out["down_payment"] = 0.0
    return out


def insert_listing(record: dict) -> int:
    rec = _clean_record(record)
    cols = EDITABLE_COLUMNS + ["created_at", "updated_at"]
    rec["created_at"] = _now()
    rec["updated_at"] = _now()
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO listings ({', '.join(cols)}) VALUES ({placeholders})"
    with get_conn() as conn:
        cur = conn.execute(sql, [rec.get(c) for c in cols])
        return cur.lastrowid


def update_listing(listing_id: int, record: dict) -> None:
    rec = _clean_record(record)
    rec["updated_at"] = _now()
    cols = EDITABLE_COLUMNS + ["updated_at"]
    assignments = ", ".join(f"{c} = ?" for c in cols)
    sql = f"UPDATE listings SET {assignments} WHERE id = ?"
    with get_conn() as conn:
        conn.execute(sql, [rec.get(c) for c in cols] + [listing_id])


def delete_listing(listing_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM listings WHERE id = ?", (listing_id,))


def delete_all() -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM listings")


def delete_seeded_listings() -> int:
    """Remove rows that were not produced by the crawler (sample/manual seed)."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM listings WHERE crawl_source_id IS NULL")
        return cur.rowcount or 0


def bulk_insert(records: list[dict]) -> int:
    inserted = 0
    cols = EDITABLE_COLUMNS + ["created_at", "updated_at"]
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO listings ({', '.join(cols)}) VALUES ({placeholders})"
    with get_conn() as conn:
        for record in records:
            rec = _clean_record(record)
            rec["created_at"] = _now()
            rec["updated_at"] = _now()
            conn.execute(sql, [rec.get(c) for c in cols])
            inserted += 1
    return inserted


def get_listing(listing_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
        return dict(row) if row else None


def fetch_df(active_only: bool = False) -> pd.DataFrame:
    """Return all listings as a DataFrame with computed metric columns."""
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT * FROM listings ORDER BY featured DESC, id DESC", conn)
    if active_only and not df.empty:
        df = df[df["status"] == "active"].reset_index(drop=True)
    return df


def distinct_values(column: str, active_only: bool = True) -> list:
    df = fetch_df(active_only=active_only)
    if df.empty or column not in df.columns:
        return []
    vals = sorted(v for v in df[column].dropna().unique().tolist() if str(v).strip())
    return vals


# --------------------------------------------------------------- inquiries
def insert_inquiry(record: dict) -> int:
    cols = ["listing_id", "listing_label", "customer_name", "customer_email",
            "customer_phone", "message", "status", "admin_notes",
            "created_at", "updated_at"]
    rec = dict(record)
    rec.setdefault("status", "New")
    rec["created_at"] = _now()
    rec["updated_at"] = _now()
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO inquiries ({', '.join(cols)}) VALUES ({placeholders})"
    with get_conn() as conn:
        cur = conn.execute(sql, [rec.get(c) for c in cols])
        return cur.lastrowid


def fetch_inquiries_df() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM inquiries ORDER BY id DESC", conn)


def get_inquiry(inquiry_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
        return dict(row) if row else None


def update_inquiry(inquiry_id: int, fields: dict) -> None:
    allowed = {"status", "admin_notes", "customer_name", "customer_email",
               "customer_phone", "message"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return
    sets["updated_at"] = _now()
    assignments = ", ".join(f"{k} = ?" for k in sets)
    sql = f"UPDATE inquiries SET {assignments} WHERE id = ?"
    with get_conn() as conn:
        conn.execute(sql, list(sets.values()) + [inquiry_id])


def delete_inquiry(inquiry_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM inquiries WHERE id = ?", (inquiry_id,))


def count_inquiries(status: str | None = None) -> int:
    with get_conn() as conn:
        if status:
            return conn.execute("SELECT COUNT(*) FROM inquiries WHERE status = ?",
                                (status,)).fetchone()[0]
        return conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]


# --------------------------------------------------------- crawl sources / runs
def insert_crawl_source(record: dict) -> int:
    cols = ["name", "url", "parser_kind", "config", "enabled",
            "location", "dealer_name", "created_at"]
    rec = dict(record)
    rec.setdefault("parser_kind", "generic")
    rec.setdefault("config", None)
    rec.setdefault("location", None)
    rec.setdefault("dealer_name", None)
    rec["enabled"] = int(rec.get("enabled", 1))
    rec["created_at"] = _now()
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO crawl_sources ({', '.join(cols)}) VALUES ({placeholders})"
    with get_conn() as conn:
        return conn.execute(sql, [rec.get(c) for c in cols]).lastrowid


def fetch_crawl_sources_df() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query("SELECT * FROM crawl_sources ORDER BY id DESC", conn)


def get_crawl_source(source_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM crawl_sources WHERE id = ?", (source_id,)
        ).fetchone()
        return dict(row) if row else None


def update_crawl_source(source_id: int, fields: dict) -> None:
    allowed = {"name", "url", "parser_kind", "config", "enabled",
               "location", "dealer_name", "last_run_at", "last_status"}
    sets = {k: (int(v) if k == "enabled" else v) for k, v in fields.items() if k in allowed}
    if not sets:
        return
    assignments = ", ".join(f"{k} = ?" for k in sets)
    sql = f"UPDATE crawl_sources SET {assignments} WHERE id = ?"
    with get_conn() as conn:
        conn.execute(sql, list(sets.values()) + [source_id])


def delete_crawl_source(source_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM crawl_sources WHERE id = ?", (source_id,))


def insert_crawl_run(record: dict) -> int:
    cols = ["source_id", "started_at", "finished_at", "fetched_pages",
            "new_listings", "updated_listings", "status", "error_message"]
    rec = dict(record)
    rec.setdefault("started_at", _now())
    placeholders = ", ".join("?" for _ in cols)
    sql = f"INSERT INTO crawl_runs ({', '.join(cols)}) VALUES ({placeholders})"
    with get_conn() as conn:
        return conn.execute(sql, [rec.get(c) for c in cols]).lastrowid


def fetch_crawl_runs_df(source_id: int | None = None, limit: int = 20) -> pd.DataFrame:
    with get_conn() as conn:
        if source_id is not None:
            return pd.read_sql_query(
                "SELECT * FROM crawl_runs WHERE source_id = ? ORDER BY id DESC LIMIT ?",
                conn, params=(source_id, limit),
            )
        return pd.read_sql_query(
            "SELECT * FROM crawl_runs ORDER BY id DESC LIMIT ?", conn, params=(limit,),
        )


def upsert_crawled_listing(source_id: int, external_id: str, record: dict) -> str:
    """Insert a crawled listing or update if (source_id, external_id) already exists.
    Returns 'inserted' or 'updated'."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM listings WHERE crawl_source_id = ? AND external_id = ?",
            (source_id, external_id),
        ).fetchone()
        if row:
            rec = _clean_record(record)
            rec["last_seen_at"] = _now()
            rec["updated_at"] = _now()
            cols = EDITABLE_COLUMNS + ["last_seen_at", "updated_at"]
            assignments = ", ".join(f"{c} = ?" for c in cols)
            conn.execute(
                f"UPDATE listings SET {assignments} WHERE id = ?",
                [rec.get(c) for c in cols] + [row[0]],
            )
            return "updated"
        # New row
        rec = _clean_record(record)
        rec["created_at"] = _now()
        rec["updated_at"] = _now()
        rec["last_seen_at"] = _now()
        cols = EDITABLE_COLUMNS + ["created_at", "updated_at",
                                   "crawl_source_id", "external_id", "last_seen_at"]
        rec["crawl_source_id"] = source_id
        rec["external_id"] = external_id
        placeholders = ", ".join("?" for _ in cols)
        conn.execute(
            f"INSERT INTO listings ({', '.join(cols)}) VALUES ({placeholders})",
            [rec.get(c) for c in cols],
        )
        return "inserted"
