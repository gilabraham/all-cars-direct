"""Admin — bulk import listings from CSV."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth, db, seed, styles
from lib.icons import icon

styles.hero("Bulk CSV upload", "Import your whole inventory at once. Validate, preview, then commit.",
            icon_svg=icon("upload", 30, "#ffffff"))

if not auth.require_admin():
    st.stop()

REQUIRED = ["make", "model", "year"]

# ----------------------------------------------------------- instructions
with st.expander("Expected columns & format", expanded=False, icon=":material/menu_book:"):
    st.markdown(
        "Your CSV may include any of the columns below. Only **make**, **model**, and "
        "**year** are required; everything else is optional. Unknown columns are ignored. "
        "Leave numeric cells blank when not applicable (e.g. money factor on a cash deal)."
    )
    schema = pd.DataFrame(
        [
            ("make", "text", "Yes", "Toyota"),
            ("model", "text", "Yes", "RAV4"),
            ("year", "integer", "Yes", "2025"),
            ("trim", "text", "", "XLE Premium"),
            ("body_type", "text", "", "SUV / Sedan / Truck …"),
            ("deal_type", "text", "", "Lease / Finance / Cash"),
            ("fuel_type", "text", "", "Gas / Hybrid / Electric …"),
            ("monthly_payment", "number", "", "329"),
            ("down_payment", "number", "", "1995"),
            ("term_months", "integer", "", "36"),
            ("annual_mileage", "integer", "", "12000"),
            ("msrp", "number", "", "35420"),
            ("selling_price", "number", "", "34100"),
            ("money_factor", "number", "", "0.00150"),
            ("residual_percent", "number", "", "62"),
            ("exterior_color", "text", "", "Lunar Rock"),
            ("location", "text", "", "Los Angeles, CA"),
            ("dealer_name", "text", "", "Toyota of Downtown LA"),
            ("image_url", "text", "", "https://… (blank = auto image)"),
            ("description", "text", "", "Loyalty cash applied"),
            ("featured", "0/1", "", "1"),
            ("status", "text", "", "active / inactive / sold"),
        ],
        columns=["Column", "Type", "Required", "Example"],
    )
    st.dataframe(schema, width="stretch", hide_index=True)

c1, c2 = st.columns(2)
with c1:
    st.download_button("Download blank template", seed.template_csv_bytes(),
                       file_name="all_cars_direct_template.csv", mime="text/csv",
                       width="stretch", icon=":material/download:")
with c2:
    st.download_button("Download sample inventory", seed.sample_csv_bytes(),
                       file_name="all_cars_direct_sample_inventory.csv", mime="text/csv",
                       width="stretch", icon=":material/download:")

st.divider()

# ----------------------------------------------------------------- uploader
uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
if uploaded is None:
    st.info("Choose a CSV above to begin. Use the template if you're starting from scratch.")
    st.stop()

try:
    raw = pd.read_csv(uploaded)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not read CSV: {exc}")
    st.stop()

# Normalise headers.
raw.columns = [str(c).strip().lower().replace(" ", "_") for c in raw.columns]

known = set(db.EDITABLE_COLUMNS)
present = [c for c in raw.columns if c in known]
unknown = [c for c in raw.columns if c not in known]
missing_required = [c for c in REQUIRED if c not in raw.columns]

styles.asection("Step 1 — File summary", "inbox")
styles.metric_cards([
    ("layers", len(raw), "Rows in file", "#0E2A47"),
    ("check-circle", len(present), "Recognized columns", "#16a34a"),
    ("tag", len(unknown), "Ignored columns", "#94a3b8"),
])
if unknown:
    st.caption("Ignored columns: " + ", ".join(unknown))

if missing_required:
    st.error("Missing required column(s): " + ", ".join(missing_required) +
             ". Add them and re-upload.")
    st.stop()

# ----------------------------------------------------------------- validation
work = raw[present].copy()
for col in db.EDITABLE_COLUMNS:
    if col not in work.columns:
        work[col] = None

def _row_errors(row) -> list[str]:
    errs = []
    if not str(row.get("make") or "").strip():
        errs.append("missing make")
    if not str(row.get("model") or "").strip():
        errs.append("missing model")
    try:
        int(float(row.get("year")))
    except (TypeError, ValueError):
        errs.append("invalid year")
    dt = str(row.get("deal_type") or "").strip()
    if dt and dt.title() not in db.DEAL_TYPES:
        errs.append(f"unknown deal_type '{dt}'")
    return errs

work["_errors"] = work.apply(_row_errors, axis=1)
valid = work[work["_errors"].str.len() == 0].copy()
invalid = work[work["_errors"].str.len() > 0].copy()

styles.asection("Step 2 — Validation", "check-circle")
styles.metric_cards([
    ("check-circle", len(valid), "Valid rows", "#16a34a"),
    ("bell", len(invalid), "Rows with issues", "#f59e0b"),
])

if not invalid.empty:
    show_inv = invalid.copy()
    show_inv["issues"] = show_inv["_errors"].apply(lambda e: ", ".join(e))
    st.warning("These rows will be skipped on import:")
    st.dataframe(show_inv[["make", "model", "year", "issues"]],
                 width="stretch", hide_index=True)

styles.asection("Step 3 — Preview valid rows", "directions_car")
if valid.empty:
    st.error("No valid rows to import.")
    st.stop()
preview_cols = ["make", "model", "year", "trim", "deal_type",
                "monthly_payment", "down_payment", "term_months", "msrp", "selling_price"]
st.dataframe(valid[preview_cols], width="stretch", hide_index=True)

# ------------------------------------------------------------------- commit
styles.asection("Step 4 — Import", "upload")
mode = st.radio(
    "Import mode",
    ["Append to existing inventory", "Replace ALL existing inventory"],
    horizontal=True,
)
replace = mode.startswith("Replace")
if replace:
    st.warning(f"This deletes all {db.count_listings()} current listing(s) before importing.")

if st.button(f"Import {len(valid)} listing(s)", type="primary", icon=":material/publish:"):
    records = valid[db.EDITABLE_COLUMNS].to_dict(orient="records")
    if replace:
        db.delete_all()
    inserted = db.bulk_insert(records)
    st.success(f"Imported {inserted} listing(s)"
               + (" (replaced existing inventory)." if replace else ".")
               + " View them on the **Browse Deals** page.")
    st.toast("Import complete", icon=":material/check_circle:")
