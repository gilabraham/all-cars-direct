"""Admin — create, edit, and delete listings."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth, db, styles
from lib.icons import icon
from lib.images import image_src, to_data_uri
from lib.ui import title_for

styles.hero("Manage listings", "Add, edit, or remove inventory. Changes are live immediately.",
            icon_svg=icon("build", 30, "#ffffff"))

if not auth.require_admin():
    st.stop()

_all = db.fetch_df(active_only=False)
_n_featured = int((_all["featured"] == 1).sum()) if not _all.empty else 0
styles.metric_cards([
    ("layers", len(_all), "Total listings", "#0E2A47"),
    ("check-circle", int((_all["status"] == "active").sum()) if not _all.empty else 0, "Active", "#16a34a"),
    ("star", _n_featured, "Featured", "#f59e0b"),
    ("tag", _all["make"].nunique() if not _all.empty else 0, "Brands", "#db2777"),
])


def _options(column: str, base: list[str]) -> list[str]:
    existing = db.distinct_values(column, active_only=False)
    return sorted(set(base) | {str(v) for v in existing if str(v).strip()})


tab_grid, tab_add, tab_edit = st.tabs([
    ":material/table_chart: Spreadsheet editor",
    ":material/add: Add listing",
    ":material/edit: Edit / delete",
])

# ============================================================ spreadsheet edit
with tab_grid:
    st.caption("Edit cells inline, add rows at the bottom, or select rows to delete — "
               "then click **Save changes**.")
    df = db.fetch_df(active_only=False)
    grid_cols = ["id"] + db.EDITABLE_COLUMNS
    if df.empty:
        df = pd.DataFrame(columns=grid_cols)
    grid_df = df.reindex(columns=grid_cols).copy()
    grid_df["featured"] = grid_df["featured"].fillna(0).astype(bool)

    column_config = {
        "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
        "make": st.column_config.TextColumn("Make", required=True),
        "model": st.column_config.TextColumn("Model", required=True),
        "year": st.column_config.NumberColumn("Year", min_value=1980, max_value=2100, step=1, required=True),
        "deal_type": st.column_config.SelectboxColumn("Type", options=_options("deal_type", db.DEAL_TYPES)),
        "body_type": st.column_config.SelectboxColumn("Body", options=_options("body_type", db.BODY_TYPES)),
        "fuel_type": st.column_config.SelectboxColumn("Fuel", options=_options("fuel_type", db.FUEL_TYPES)),
        "status": st.column_config.SelectboxColumn("Status", options=_options("status", db.STATUSES)),
        "monthly_payment": st.column_config.NumberColumn("Monthly", format="$%d"),
        "down_payment": st.column_config.NumberColumn("Down", format="$%d"),
        "term_months": st.column_config.NumberColumn("Term", step=1),
        "annual_mileage": st.column_config.NumberColumn("Miles/yr", step=500),
        "msrp": st.column_config.NumberColumn("MSRP", format="$%d"),
        "selling_price": st.column_config.NumberColumn("Sale", format="$%d"),
        "money_factor": st.column_config.NumberColumn("MF", format="%.5f"),
        "residual_percent": st.column_config.NumberColumn("Residual %", format="%.0f"),
        "featured": st.column_config.CheckboxColumn("Featured"),
        "image_url": st.column_config.ImageColumn("Photo", help="Uploaded/linked photo (edit in the Add/Edit tabs)"),
    }

    edited = st.data_editor(
        grid_df, key="grid_editor", num_rows="dynamic",
        width="stretch", hide_index=True, column_config=column_config,
        height=460,
    )

    if st.button("Save changes", type="primary", icon=":material/save:"):
        changes = st.session_state.get("grid_editor", {})
        n_upd = n_add = n_del = 0
        # Updates
        for idx, ch in changes.get("edited_rows", {}).items():
            base = grid_df.iloc[int(idx)].to_dict()
            base.update(ch)
            db.update_listing(int(base["id"]), base)
            n_upd += 1
        # Additions
        for row in changes.get("added_rows", []):
            if row.get("make") and row.get("model") and row.get("year"):
                db.insert_listing(row)
                n_add += 1
        # Deletions
        for idx in changes.get("deleted_rows", []):
            rid = grid_df.iloc[int(idx)]["id"]
            if pd.notna(rid):
                db.delete_listing(int(rid))
                n_del += 1
        st.success(f"Saved — {n_add} added, {n_upd} updated, {n_del} deleted.")
        st.rerun()

# ===================================================================== add form
with tab_add:
    with st.form("add_listing", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            make = st.text_input("Make *")
            model = st.text_input("Model *")
            year = st.number_input("Year *", min_value=1980, max_value=2100, value=2025, step=1)
            trim = st.text_input("Trim")
            body_type = st.selectbox("Body type", _options("body_type", db.BODY_TYPES), index=0)
            fuel_type = st.selectbox("Fuel type", _options("fuel_type", db.FUEL_TYPES), index=0)
        with c2:
            deal_type = st.selectbox("Deal type", db.DEAL_TYPES, index=0)
            monthly_payment = st.number_input("Monthly payment ($)", min_value=0.0, value=None, step=10.0)
            down_payment = st.number_input("Down / due at signing ($)", min_value=0.0, value=0.0, step=100.0)
            term_months = st.number_input("Term (months)", min_value=0, value=None, step=1)
            annual_mileage = st.number_input("Annual mileage", min_value=0, value=None, step=500)
            money_factor = st.number_input("Money factor", min_value=0.0, value=None, step=0.0001, format="%.5f")
        with c3:
            msrp = st.number_input("MSRP ($)", min_value=0.0, value=None, step=100.0)
            selling_price = st.number_input("Selling price ($)", min_value=0.0, value=None, step=100.0)
            residual_percent = st.number_input("Residual (%)", min_value=0.0, max_value=100.0, value=None, step=1.0)
            exterior_color = st.text_input("Exterior color")
            location = st.text_input("Location")
            dealer_name = st.text_input("Dealer name")
        image_url = st.text_input("Image URL (optional)",
                                  help="Paste a URL, upload a photo below, or leave blank for an auto image.")
        add_photo = st.file_uploader("Or upload a photo", type=["png", "jpg", "jpeg", "webp"])
        description = st.text_area("Description / notes")
        col_a, col_b = st.columns(2)
        with col_a:
            featured = st.checkbox(":material/star: Featured")
        with col_b:
            status = st.selectbox("Status", db.STATUSES, index=0)

        submitted = st.form_submit_button("Add listing", type="primary", icon=":material/add:")
    if submitted:
        if not (make and model):
            st.error("Make and Model are required.")
        else:
            final_image = to_data_uri(add_photo) if add_photo is not None else image_url
            db.insert_listing({
                "make": make, "model": model, "year": year, "trim": trim,
                "body_type": body_type, "fuel_type": fuel_type, "deal_type": deal_type,
                "monthly_payment": monthly_payment, "down_payment": down_payment,
                "term_months": term_months, "annual_mileage": annual_mileage,
                "msrp": msrp, "selling_price": selling_price, "money_factor": money_factor,
                "residual_percent": residual_percent, "exterior_color": exterior_color,
                "location": location, "dealer_name": dealer_name, "image_url": final_image,
                "description": description, "featured": int(featured), "status": status,
            })
            st.success(f"Added {year} {make} {model}.")

# ============================================================== edit / delete
with tab_edit:
    df = db.fetch_df(active_only=False)
    if df.empty:
        st.info("No listings to edit yet.")
    else:
        df["label"] = df.apply(lambda r: f"#{r['id']} · {title_for(r)} — {r.get('trim') or ''} ({r['deal_type']})", axis=1)
        choice = st.selectbox("Select a listing", df["label"].tolist())
        rid = int(df[df["label"] == choice]["id"].iloc[0])
        rec = db.get_listing(rid)

        _current_img = rec.get("image_url") or ""
        _is_data = _current_img.startswith("data:")
        st.image(image_src(rec.get("make"), rec.get("model"), rec.get("year"), _current_img),
                 width=280, caption="Current photo")

        def _idx(options, value, default=0):
            try:
                return options.index(value)
            except (ValueError, AttributeError):
                return default

        with st.form("edit_listing"):
            c1, c2, c3 = st.columns(3)
            with c1:
                make = st.text_input("Make *", rec.get("make") or "")
                model = st.text_input("Model *", rec.get("model") or "")
                year = st.number_input("Year *", 1980, 2100, int(rec.get("year") or 2025), step=1)
                trim = st.text_input("Trim", rec.get("trim") or "")
                body_opts = _options("body_type", db.BODY_TYPES)
                body_type = st.selectbox("Body type", body_opts, index=_idx(body_opts, rec.get("body_type")))
                fuel_opts = _options("fuel_type", db.FUEL_TYPES)
                fuel_type = st.selectbox("Fuel type", fuel_opts, index=_idx(fuel_opts, rec.get("fuel_type")))
            with c2:
                deal_type = st.selectbox("Deal type", db.DEAL_TYPES, index=_idx(db.DEAL_TYPES, rec.get("deal_type")))
                monthly_payment = st.number_input("Monthly payment ($)", min_value=0.0,
                                                  value=float(rec["monthly_payment"]) if rec.get("monthly_payment") is not None else None, step=10.0)
                down_payment = st.number_input("Down / due at signing ($)", min_value=0.0,
                                               value=float(rec.get("down_payment") or 0.0), step=100.0)
                term_months = st.number_input("Term (months)", min_value=0,
                                              value=int(rec["term_months"]) if rec.get("term_months") is not None else None, step=1)
                annual_mileage = st.number_input("Annual mileage", min_value=0,
                                                 value=int(rec["annual_mileage"]) if rec.get("annual_mileage") is not None else None, step=500)
                money_factor = st.number_input("Money factor", min_value=0.0,
                                               value=float(rec["money_factor"]) if rec.get("money_factor") is not None else None, step=0.0001, format="%.5f")
            with c3:
                msrp = st.number_input("MSRP ($)", min_value=0.0,
                                       value=float(rec["msrp"]) if rec.get("msrp") is not None else None, step=100.0)
                selling_price = st.number_input("Selling price ($)", min_value=0.0,
                                                value=float(rec["selling_price"]) if rec.get("selling_price") is not None else None, step=100.0)
                residual_percent = st.number_input("Residual (%)", min_value=0.0, max_value=100.0,
                                                   value=float(rec["residual_percent"]) if rec.get("residual_percent") is not None else None, step=1.0)
                exterior_color = st.text_input("Exterior color", rec.get("exterior_color") or "")
                location = st.text_input("Location", rec.get("location") or "")
                dealer_name = st.text_input("Dealer name", rec.get("dealer_name") or "")
            image_url = st.text_input("Image URL", "" if _is_data else _current_img,
                                      help="Paste a URL, or upload below to replace.")
            edit_photo = st.file_uploader("Replace photo (upload)", type=["png", "jpg", "jpeg", "webp"])
            clear_photo = st.checkbox("Remove current photo (use auto image)") if _current_img else False
            description = st.text_area("Description / notes", rec.get("description") or "")
            col_a, col_b = st.columns(2)
            with col_a:
                featured = st.checkbox(":material/star: Featured", value=bool(rec.get("featured")))
            with col_b:
                status = st.selectbox("Status", db.STATUSES, index=_idx(db.STATUSES, rec.get("status")))
            save = st.form_submit_button("Save changes", type="primary", icon=":material/save:")
        if save:
            if clear_photo:
                final_image = ""
            elif edit_photo is not None:
                final_image = to_data_uri(edit_photo)
            elif image_url.strip():
                final_image = image_url.strip()
            elif _is_data:
                final_image = _current_img  # keep existing uploaded photo
            else:
                final_image = ""
            db.update_listing(rid, {
                "make": make, "model": model, "year": year, "trim": trim,
                "body_type": body_type, "fuel_type": fuel_type, "deal_type": deal_type,
                "monthly_payment": monthly_payment, "down_payment": down_payment,
                "term_months": term_months, "annual_mileage": annual_mileage,
                "msrp": msrp, "selling_price": selling_price, "money_factor": money_factor,
                "residual_percent": residual_percent, "exterior_color": exterior_color,
                "location": location, "dealer_name": dealer_name, "image_url": final_image,
                "description": description, "featured": int(featured), "status": status,
            })
            st.success("Saved.")
            st.rerun()

        st.divider()
        with st.expander("Delete this listing", icon=":material/delete:"):
            st.warning(f"This permanently removes **{choice}**.")
            confirm = st.checkbox("Yes, I'm sure", key="confirm_del")
            if st.button("Delete listing", disabled=not confirm):
                db.delete_listing(rid)
                st.success("Listing deleted.")
                st.rerun()

# ============================================================== danger zone
st.divider()
with st.expander("Danger zone — delete ALL listings", icon=":material/warning:"):
    st.error("This wipes every listing in the database. There is no undo.")
    typed = st.text_input("Type DELETE ALL to confirm")
    if st.button("Wipe all listings", disabled=(typed != "DELETE ALL")):
        db.delete_all()
        st.success("All listings deleted.")
        st.rerun()
