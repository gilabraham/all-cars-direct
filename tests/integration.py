"""Exercise the data-mutation flows against a throwaway database."""
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from lib import db, seed, scoring  # noqa: E402

# Redirect the DB to a temp file so we don't touch real data.
tmp = Path(tempfile.mkdtemp()) / "test.db"
db.DB_PATH = tmp
db.DATA_DIR = tmp.parent
db.init_db()
assert db.count_listings() == 0, "fresh db should be empty"

# 1. Seed
n = seed.seed_if_empty()
assert n == db.count_listings() and n > 0, "seed should populate"
print(f"seed: {n} rows")

# 2. Insert a single listing
new_id = db.insert_listing({
    "make": "Polestar", "model": "2", "year": 2026, "deal_type": "Lease",
    "monthly_payment": 399, "down_payment": 2999, "term_months": 24,
    "annual_mileage": 10000, "msrp": 51900, "selling_price": 49900,
    "fuel_type": "Electric", "body_type": "Sedan", "featured": True,
})
rec = db.get_listing(new_id)
assert rec["make"] == "Polestar" and rec["featured"] == 1, "insert + featured cast"
print(f"insert: id={new_id} featured={rec['featured']}")

# 3. Update
db.update_listing(new_id, {**rec, "monthly_payment": 359, "status": "inactive"})
rec2 = db.get_listing(new_id)
assert rec2["monthly_payment"] == 359 and rec2["status"] == "inactive", "update applied"
print(f"update: monthly={rec2['monthly_payment']} status={rec2['status']}")

# 4. active_only filter excludes inactive
active = db.fetch_df(active_only=True)
assert new_id not in active["id"].values, "inactive excluded from active view"
print(f"active filter: {len(active)} active of {db.count_listings()} total")

# 5. CSV bulk import (simulate upload: normalize headers, validate, bulk_insert)
csv_bytes = seed.template_csv_bytes()
raw = pd.read_csv(io.BytesIO(csv_bytes))
raw.columns = [str(c).strip().lower().replace(" ", "_") for c in raw.columns]
present = [c for c in raw.columns if c in set(db.EDITABLE_COLUMNS)]
work = raw[present].copy()
before = db.count_listings()
inserted = db.bulk_insert(work.to_dict(orient="records"))
assert db.count_listings() == before + inserted == before + len(raw), "bulk import count"
print(f"bulk import: +{inserted} rows")

# 6. Cash deal (no monthly) imports & scores without crashing
cash_id = db.insert_listing({
    "make": "Lucid", "model": "Air", "year": 2026, "deal_type": "Cash",
    "selling_price": 71000, "msrp": 74000, "fuel_type": "Electric", "body_type": "Sedan",
})
df = scoring.enrich(db.fetch_df())
crow = df[df["id"] == cash_id].iloc[0]
assert pd.isna(crow["effective_monthly"]) or crow["effective_monthly"] is None
print(f"cash deal: discount={crow['discount_percent']:.1f}% eff_monthly handled")

# 7. Delete
db.delete_listing(new_id)
assert db.get_listing(new_id) is None, "delete removed row"
print("delete: ok")

# 8. Wipe all
db.delete_all()
assert db.count_listings() == 0, "delete_all clears table"
print("delete_all: ok")

print("-" * 40)
print("INTEGRATION FLOWS PASSED ✅")
