"""Admin — manage customer deal requests (inquiries)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import auth, db, mailer, styles
from lib.icons import icon

styles.hero("Customer requests", "Deal inquiries from shoppers — track and manage follow-ups.",
            icon_svg=icon("inbox", 30, "#ffffff"))

if not auth.require_admin():
    st.stop()

if not mailer.is_configured():
    st.caption(":material/info: Email delivery isn't configured, so confirmations aren't auto-sent. "
               "Requests are still captured below. Add SMTP settings to `.streamlit/secrets.toml` to enable email.")

idf = db.fetch_inquiries_df()

def _count(s):
    return int((idf["status"] == s).sum()) if not idf.empty else 0

styles.metric_cards([
    ("inbox", len(idf), "Total", "#0E2A47"),
    ("bell", _count("New"), "New", "#f59e0b"),
    ("phone", _count("Contacted"), "Contacted", "#0ea5e9"),
    ("check-circle", _count("Closed"), "Closed", "#16a34a"),
])

if idf.empty:
    st.info("No requests yet. They'll appear here when customers submit the "
            "**Request this deal** form on a listing.")
    st.stop()

# Friendly received date.
idf["received"] = pd.to_datetime(idf["created_at"], errors="coerce").dt.strftime("%b %d, %Y %H:%M")

st.divider()
styles.asection("Incoming requests", "inbox")
status_filter = st.segmented_control("Show", ["All"] + db.INQUIRY_STATUSES, default="All",
                                     key="req_status_filter")
view = idf if status_filter in (None, "All") else idf[idf["status"] == status_filter]

table = view[["id", "received", "customer_name", "customer_email", "customer_phone",
              "listing_label", "status"]].copy()
table.columns = ["ID", "Received", "Name", "Email", "Phone", "Vehicle", "Status"]
st.dataframe(
    table, width="stretch", hide_index=True,
    column_config={
        "Status": st.column_config.TextColumn(width="small"),
        "Email": st.column_config.TextColumn(width="medium"),
    },
)

if view.empty:
    st.stop()

st.divider()
styles.asection("Manage a request", "build")

id_to_label = {
    int(r["id"]): f"#{int(r['id'])} · {r['customer_name']} — {r['listing_label']} ({r['status']})"
    for _, r in view.iterrows()
}
rid = st.selectbox("Select a request", list(id_to_label), format_func=lambda i: id_to_label[i])
rec = db.get_inquiry(int(rid))

if rec:
    with st.container(border=True):
        det = [
            ("Vehicle", rec.get("listing_label") or "—"),
            ("Name", rec.get("customer_name") or "—"),
            ("Email", f"<a href='mailto:{rec.get('customer_email')}'>{rec.get('customer_email')}</a>"),
            ("Phone", rec.get("customer_phone") or "—"),
            ("Received", pd.to_datetime(rec.get("created_at"), errors="coerce").strftime("%b %d, %Y %H:%M")
                if rec.get("created_at") else "—"),
            ("Status", styles.status_badge(rec.get("status") or "New")),
        ]
        cells = "".join(f"<div><div class='k'>{k}</div><div class='v'>{v}</div></div>" for k, v in det)
        st.markdown(f"<div class='ll-detail-grid'>{cells}</div>", unsafe_allow_html=True)
        if rec.get("message"):
            st.markdown("**Customer message**")
            st.info(rec["message"])

        with st.form("manage_request"):
            idx = db.INQUIRY_STATUSES.index(rec["status"]) if rec.get("status") in db.INQUIRY_STATUSES else 0
            mc1, mc2 = st.columns([1, 2])
            with mc1:
                new_status = st.selectbox("Status", db.INQUIRY_STATUSES, index=idx)
            with mc2:
                notes = st.text_area("Internal notes", rec.get("admin_notes") or "",
                                     placeholder="Follow-up notes, next steps…")
            saved = st.form_submit_button("Save changes", type="primary", icon=":material/save:")
        if saved:
            db.update_inquiry(int(rid), {"status": new_status, "admin_notes": notes})
            st.success("Request updated.")
            st.rerun()

    with st.expander("Delete this request", icon=":material/delete:"):
        st.warning("This permanently removes the request.")
        if st.checkbox("Yes, I'm sure", key="confirm_del_req"):
            if st.button("Delete request", icon=":material/delete:"):
                db.delete_inquiry(int(rid))
                st.success("Request deleted.")
                st.rerun()
