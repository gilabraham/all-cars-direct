"""Shared ``show_detail`` dialog — opens the same deal-details modal from
any page (browse, home top-deals, etc.)."""
from __future__ import annotations

import math

import streamlit as st
import streamlit.components.v1 as components

from lib import db, mailer, scoring
from lib.icons import icon
from lib.images import image_src
from lib.ui import deal_type_color, money, num, pct, title_for


def _has_value(value) -> bool:
    """True when ``value`` is something meaningful. Treats NaN as missing —
    pandas leaves numeric NaN in optional columns (e.g. ``term_months`` is
    NaN on Cash deals), and ``if NaN`` is truthy, which bites ``int(NaN)``.
    """
    if value is None or value == "" or value == "—":
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    return True


def _fmt_or_dash(value) -> str:
    return value if _has_value(value) else "—"


_SCROLL_RESET_JS = """
<script>
  // Streamlit dialogs sometimes open with the scroll position at the bottom
  // (the form text inputs steal focus, the browser scrolls to them). Force
  // the dialog's scrollable surface back to the top after each render tick.
  const reset = () => {
    const doc = window.parent.document;
    const sels = [
      '[role="dialog"]',
      '[data-testid="stDialog"]',
      '[data-testid="stModal"]',
      '[data-testid="stDialog"] > div',
    ];
    sels.forEach(s => doc.querySelectorAll(s).forEach(el => { el.scrollTop = 0; }));
    // Blur whatever is focused so it doesn't pull us back down.
    if (doc.activeElement && doc.activeElement.tagName === 'INPUT') {
      doc.activeElement.blur();
    }
  };
  setTimeout(reset, 30);
  setTimeout(reset, 150);
  setTimeout(reset, 400);
</script>
"""


@st.dialog("Deal details", width="large")
def show_detail(row: dict):
    components.html(_SCROLL_RESET_JS, height=0)
    dt = row.get("deal_type") or "Lease"
    dt_color = deal_type_color(dt)
    rating_label, rating_color = scoring.rating(
        row.get("monthly_payment"), row.get("down_payment"),
        row.get("term_months"), row.get("msrp"),
    )
    score = scoring.deal_score(
        row.get("monthly_payment"), row.get("down_payment"),
        row.get("term_months"), row.get("msrp"),
    )
    eff = scoring.effective_monthly(
        row.get("monthly_payment"), row.get("down_payment"), row.get("term_months"),
    )
    pct_msrp = scoring.percent_of_msrp(
        row.get("monthly_payment"), row.get("down_payment"),
        row.get("term_months"), row.get("msrp"),
    )
    discount = scoring.discount_percent(row.get("selling_price"), row.get("msrp"))

    # ---- Hero: image on the left, headline + price on the right.
    img_col, info_col = st.columns([5, 7], gap="medium")
    with img_col:
        img_url = image_src(
            row.get("make"), row.get("model"),
            row.get("year"), row.get("image_url"),
        )
        st.markdown(
            f"<div class='ll-md-img'>"
            f"<img src='{img_url}' alt='{title_for(row)}'/>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with info_col:
        chips = (
            f"<span class='ll-md-chip' style='background:{dt_color}1f;color:{dt_color};"
            f"border-color:{dt_color}40;'>{dt}</span>"
            f"<span class='ll-md-chip' style='background:{rating_color}1f;color:{rating_color};"
            f"border-color:{rating_color}40;'>"
            f"{icon('star', 12, rating_color, fill=rating_color)} {rating_label}"
            + (f" · {score}/100" if score is not None else "") + "</span>"
        )
        sub_bits = [str(x) for x in (row.get("trim"), row.get("body_type"),
                    row.get("fuel_type"), row.get("exterior_color")) if x]
        subtitle = " · ".join(sub_bits)

        if dt == "Cash":
            primary_amt = money(row.get("selling_price"))
            primary_unit = "cash price"
            secondary_bits = []
            if row.get("msrp"):
                secondary_bits.append(f"MSRP {money(row.get('msrp'))}")
            if discount is not None:
                secondary_bits.append(f"{pct(discount)} off")
        else:
            primary_amt = money(row.get("monthly_payment"))
            primary_unit = f"/mo {dt.lower()}"
            secondary_bits = []
            if eff is not None:
                secondary_bits.append(f"{money(eff)} effective")
            if _has_value(row.get("term_months")):
                secondary_bits.append(f"{int(row['term_months'])} mo")
            if _has_value(row.get("down_payment")):
                secondary_bits.append(f"{money(row.get('down_payment'))} due")
        secondary = "  ·  ".join(secondary_bits) if secondary_bits else ""

        loc_bits = []
        if row.get("dealer_name"):
            loc_bits.append(row["dealer_name"])
        if row.get("location"):
            loc_bits.append(row["location"])
        loc_html = (
            f"<div class='ll-md-loc'>{icon('map-pin', 14, '#6b7686')} "
            f"{' · '.join(loc_bits)}</div>" if loc_bits else ""
        )

        st.markdown(
            f"<div class='ll-md-chips'>{chips}</div>"
            f"<h2 class='ll-md-title'>{title_for(row)}</h2>"
            + (f"<p class='ll-md-sub'>{subtitle}</p>" if subtitle else "")
            + f"<div class='ll-md-price'>"
              f"<div class='ll-md-price-row'>"
              f"<span class='ll-md-price-amt'>{primary_amt}</span>"
              f"<span class='ll-md-price-unit'>{primary_unit}</span>"
              f"</div>"
              + (f"<div class='ll-md-price-sub'>{secondary}</div>" if secondary else "")
              + f"</div>"
              + loc_html,
            unsafe_allow_html=True,
        )

    # ---- Spec sections (three grouped cards).
    pricing_specs = [
        ("MSRP", money(row.get("msrp"))),
        ("Selling price", money(row.get("selling_price"))),
        ("Discount off MSRP", pct(discount)),
        ("% of MSRP / mo", pct(pct_msrp)),
    ]
    terms_specs = [
        ("Term", f"{int(row['term_months'])} months" if _has_value(row.get("term_months")) else "—"),
        ("Annual mileage", num(row.get("annual_mileage"))),
        ("Due at signing", money(row.get("down_payment"))),
        ("Money factor",
         _fmt_or_dash(row.get("money_factor")) if row.get("money_factor") else "—"),
        ("Residual", pct(row.get("residual_percent"))),
    ]
    vehicle_specs = [
        ("Body type", _fmt_or_dash(row.get("body_type"))),
        ("Fuel", _fmt_or_dash(row.get("fuel_type"))),
        ("Color", _fmt_or_dash(row.get("exterior_color"))),
        ("Location", _fmt_or_dash(row.get("location"))),
        ("Dealer", _fmt_or_dash(row.get("dealer_name"))),
    ]

    def _spec_card(title: str, ic: str, items) -> str:
        rows_html = "".join(
            f"<div class='ll-md-spec-row'><span class='k'>{k}</span>"
            f"<span class='v'>{v}</span></div>"
            for k, v in items
        )
        return (
            f"<section class='ll-md-spec-card'>"
            f"<h4>{icon(ic, 16, '#2E8BFF')} {title}</h4>"
            f"{rows_html}"
            f"</section>"
        )

    st.markdown(
        "<div class='ll-md-specs'>"
        + _spec_card("Pricing", "tag", pricing_specs)
        + _spec_card("Terms", "percent", terms_specs)
        + _spec_card("Vehicle & dealer", "info", vehicle_specs)
        + "</div>",
        unsafe_allow_html=True,
    )

    if row.get("description"):
        st.markdown(
            f"<div class='ll-md-desc'>{row['description']}</div>",
            unsafe_allow_html=True,
        )

    # ---- Request form.
    st.markdown(
        f"<div class='ll-md-req-head'>"
        f"<div class='ll-md-req-ic'>{icon('phone', 18, '#ffffff')}</div>"
        f"<div><h3>Request this deal</h3>"
        f"<p>A specialist confirms availability and locks in pricing within 24 hours.</p></div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    with st.container(key=f"md_req_wrap_{row['id']}"):
        with st.form(f"request_form_{row['id']}"):
            name = st.text_input("Your name *")
            fc1, fc2 = st.columns(2)
            with fc1:
                email = st.text_input("Email *")
            with fc2:
                phone = st.text_input("Phone")
            msg = st.text_area("Anything we should know? (optional)",
                               placeholder="Preferred color, timing, trade-in, questions…")
            sent_clicked = st.form_submit_button(
                "Send request", type="primary", icon=":material/send:",
            )
    if sent_clicked:
        valid_email = "@" in email and "." in email.split("@")[-1]
        if not name.strip() or not valid_email:
            st.error("Please enter your name and a valid email address.")
        else:
            label = f"{title_for(row)} ({dt})"
            payload = {
                "listing_id": int(row["id"]), "listing_label": label,
                "customer_name": name.strip(), "customer_email": email.strip(),
                "customer_phone": phone.strip(), "message": msg.strip(),
            }
            db.insert_inquiry(payload)
            ok, _ = mailer.send_request_emails(payload)
            st.session_state["req_toast"] = (
                "Request sent — confirmation emailed!" if ok
                else "Request sent! We'll be in touch shortly."
            )
            st.rerun()
