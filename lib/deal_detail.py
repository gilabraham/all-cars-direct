"""Shared ``show_detail`` dialog — opens the same deal-details modal from
any page (browse, home top-deals, etc.)."""
from __future__ import annotations

import json
import math
import re

import streamlit as st
import streamlit.components.v1 as components

from lib import db, mailer, scoring
from lib.icons import icon
from lib.images import image_src
from lib.ui import (DEAL_PRIORITY, available_deal_types, deal_type_color,
                    featured_deal_for, money, num, pct, title_for)


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


def _cash_value(row: dict):
    """``cash_price`` is the headless-scraped sticker; ``selling_price`` is the
    static dealer-page price. Prefer the former but NaN-safely fall back.
    Plain ``or`` is wrong here — NaN is truthy in Python."""
    cp = row.get("cash_price")
    if cp is not None and not (isinstance(cp, float) and math.isnan(cp)):
        return cp
    return row.get("selling_price")


def _tab_headline(deal: str, row: dict) -> str:
    """One-line price shown inside each tab label so the customer can compare
    Lease/Finance/Cash before clicking through."""
    if deal == "Lease" and _has_value(row.get("lease_monthly")):
        return f"{money(row['lease_monthly'])}/mo"
    if deal == "Finance" and _has_value(row.get("finance_monthly")):
        return f"{money(row['finance_monthly'])}/mo"
    if deal == "Cash":
        cv = _cash_value(row)
        if _has_value(cv):
            return money(cv)
    return "—"


def _pricing_block_html(deal: str, row: dict) -> str:
    """One pricing card per deal type — mirrors the Coral-Springs PDP layout:
    a big primary price on top, supporting terms below."""
    cash_p = _cash_value(row)
    if deal == "Lease":
        amt = money(row.get("lease_monthly"))
        unit = "/mo lease"
        term = row.get("lease_term_months")
        down = row.get("lease_down_payment")
        rows = []
        if _has_value(term):
            rows.append(("Term", f"{int(term)} months"))
        if _has_value(down):
            rows.append(("Due at signing", money(down)))
        if _has_value(row.get("annual_mileage")):
            rows.append(("Annual mileage", num(row.get("annual_mileage"))))
        if _has_value(row.get("residual_percent")):
            rows.append(("Residual", pct(row.get("residual_percent"))))
        if _has_value(row.get("money_factor")):
            rows.append(("Money factor", _fmt_or_dash(row.get("money_factor"))))
    elif deal == "Finance":
        amt = money(row.get("finance_monthly"))
        unit = "/mo finance"
        term = row.get("finance_term_months")
        down = row.get("finance_down_payment")
        apr = row.get("finance_apr")
        rows = []
        if _has_value(term):
            rows.append(("Term", f"{int(term)} months"))
        if _has_value(down):
            rows.append(("Down payment", money(down)))
        if _has_value(apr):
            rows.append(("APR", f"{apr:.2f}%"))
        if _has_value(row.get("msrp")):
            rows.append(("MSRP", money(row.get("msrp"))))
        if _has_value(cash_p):
            rows.append(("Selling price", money(cash_p)))
    else:  # Cash
        amt = money(cash_p)
        unit = "cash price"
        disc = scoring.discount_percent(cash_p, row.get("msrp"))
        rows = []
        if _has_value(row.get("msrp")):
            rows.append(("MSRP", money(row.get("msrp"))))
        if _has_value(cash_p):
            rows.append(("Selling price", money(cash_p)))
        if disc is not None:
            rows.append(("Discount off MSRP", pct(disc)))

    rows_html = "".join(
        f"<div class='ll-md-spec-row'><span class='k'>{k}</span>"
        f"<span class='v'>{v}</span></div>"
        for k, v in rows
    ) or "<div class='ll-md-spec-row'><span class='k'>—</span></div>"

    return (
        f"<div class='ll-md-deal-price'>"
        f"<span class='ll-md-deal-amt'>{amt}</span>"
        f"<span class='ll-md-deal-unit'>{unit}</span>"
        f"</div>"
        f"<div class='ll-md-deal-rows'>{rows_html}</div>"
    )


_GALLERY_NOISE_RE = re.compile(
    r"^(new|used|pre[\s-]?owned)\s+\d{4}.*?cash\s+[\d.]+\s+Month\s+\d+\s+Months?\s*$",
    re.IGNORECASE | re.DOTALL,
)


def _useful_description(row: dict) -> str:
    """Return the listing description only if it looks like real prose. The
    headless crawler synthesizes a "New 2025 GMC Sierra 1500 Pro - cash 623.03
    Month 84 Months" string when no dealer description exists — show nothing
    rather than that parser noise."""
    desc = (row.get("description") or "").strip()
    if not desc or _GALLERY_NOISE_RE.match(desc):
        return ""
    return desc


def _render_gallery(photos: list[str], alt: str) -> None:
    """Hero image + horizontally-scrollable thumb strip in one iframe. Click
    a thumb to swap the hero in place — Streamlit strips inline scripts from
    ``unsafe_allow_html``, so the whole gallery lives in a components.html
    sandbox where JS can run."""
    if not photos:
        return
    has_strip = len(photos) > 1
    photos_js = json.dumps(photos)
    thumbs_html = "".join(
        f"<button class='thumb{(' is-active' if i == 0 else '')}' "
        f"data-idx='{i}' aria-label='Photo {i + 1}'>"
        f"<img src='{p}' loading='lazy' alt=''></button>"
        for i, p in enumerate(photos)
    )
    thumbs_block = (
        f"<div class='thumbs' id='thumbs'>{thumbs_html}</div>"
        if has_strip else ""
    )
    components.html(
        f"""
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  .gallery {{ display: flex; flex-direction: column; gap: 10px; }}
  .hero {{
    background: linear-gradient(180deg, #f6f8fb 0%, #eef2f8 100%);
    border-radius: 16px; padding: 12px; border: 1px solid #e4ebf3;
    height: 240px; display: flex; align-items: center; justify-content: center;
    box-shadow: 0 1px 2px rgba(14, 42, 71, 0.04);
  }}
  .hero img {{
    max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 10px;
    transition: opacity .18s ease;
  }}
  .thumbs {{
    display: flex; gap: 8px; overflow-x: auto;
    padding: 2px 2px 10px;
    scrollbar-width: thin; scrollbar-color: #c9d2e0 transparent;
  }}
  .thumbs::-webkit-scrollbar {{ height: 6px; }}
  .thumbs::-webkit-scrollbar-thumb {{ background: #c9d2e0; border-radius: 999px; }}
  .thumb {{
    flex: 0 0 auto; width: 72px; height: 54px; padding: 0;
    border: 1.5px solid #e4ebf3; border-radius: 8px;
    overflow: hidden; background: #eef2f8; cursor: pointer;
    transition: border-color .15s ease, transform .15s ease;
  }}
  .thumb:hover {{ transform: translateY(-1px); border-color: #b9c4d4; }}
  .thumb.is-active {{ border-color: #2E8BFF; box-shadow: 0 0 0 1px #2E8BFF; }}
  .thumb img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
</style>
<div class='gallery'>
  <div class='hero'>
    <img id='hero-img' src='{photos[0]}' alt='{alt}'>
  </div>
  {thumbs_block}
</div>
<script>
  const PHOTOS = {photos_js};
  const hero = document.getElementById('hero-img');
  document.querySelectorAll('.thumb').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const idx = parseInt(btn.dataset.idx, 10);
      hero.style.opacity = '0.4';
      const swap = new Image();
      swap.onload = () => {{ hero.src = PHOTOS[idx]; hero.style.opacity = '1'; }};
      swap.src = PHOTOS[idx];
      document.querySelectorAll('.thumb').forEach(t => t.classList.remove('is-active'));
      btn.classList.add('is-active');
    }});
  }});
</script>
""",
        # Hero box (240 + 12*2 padding + 2 border = 266) plus optional 10 gap
        # + 54 thumb + 10 bottom padding + 6 scrollbar = 80. Buffer of 8px so
        # nothing clips on browsers that report subpixel rounding differently.
        height=354 if has_strip else 274,
    )


@st.dialog("Deal details", width="large")
def show_detail(row: dict):
    components.html(_SCROLL_RESET_JS, height=0)
    rating_label, rating_color = scoring.rating(
        row.get("monthly_payment"), row.get("down_payment"),
        row.get("term_months"), row.get("msrp"),
    )
    score = scoring.deal_score(
        row.get("monthly_payment"), row.get("down_payment"),
        row.get("term_months"), row.get("msrp"),
    )

    # Featured deal mirrors the card — defers to the user's deal-type
    # filter (browse view stashes it in session state).
    available = available_deal_types(row) or ["Cash"]
    featured = featured_deal_for(row)
    dt_color = deal_type_color(featured)
    pref_order = st.session_state.get("_card_deal_pref", DEAL_PRIORITY)

    # ---- Hero: image on the left, headline + chips on the right.
    img_col, info_col = st.columns([5, 7], gap="medium")
    with img_col:
        img_url = image_src(
            row.get("make"), row.get("model"),
            row.get("year"), row.get("image_url"),
        )
        # Build the photo list (hero first, then any unique extras from the
        # headless ``photos_json``). Headless crawl banks up to 12 per VIN.
        photos: list[str] = [img_url]
        photos_raw = row.get("photos_json")
        if photos_raw:
            try:
                for p in json.loads(photos_raw):
                    if isinstance(p, str) and p and p not in photos:
                        photos.append(p)
            except (json.JSONDecodeError, TypeError):
                pass
        _render_gallery(photos, title_for(row))

    with info_col:
        chips = (
            f"<span class='ll-md-chip' style='background:{dt_color}1f;color:{dt_color};"
            f"border-color:{dt_color}40;'>{featured}</span>"
            f"<span class='ll-md-chip' style='background:{rating_color}1f;color:{rating_color};"
            f"border-color:{rating_color}40;'>"
            f"{icon('star', 12, rating_color, fill=rating_color)} {rating_label}"
            + (f" · {score}/100" if score is not None else "") + "</span>"
        )
        sub_bits = [str(x) for x in (row.get("condition"), row.get("trim"),
                    row.get("body_type"), row.get("fuel_type"),
                    row.get("exterior_color")) if x]
        subtitle = " · ".join(sub_bits)

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
            + loc_html,
            unsafe_allow_html=True,
        )

    # ---- Pricing tabs (left) sit next to Vehicle & dealer (right) on desktop,
    # mirroring a typical dealer PDP — price/options on the left, specs on the
    # right. Streamlit stacks columns under ~640px so the modal still works
    # on mobile.
    tab_order = [featured] + [d for d in pref_order
                              if d in available and d != featured]
    tab_labels = [f"{d}  ·  {_tab_headline(d, row)}" for d in tab_order]
    deal_col, spec_col = st.columns([7, 5], gap="medium")
    with deal_col:
        tabs = st.tabs(tab_labels)
        for tab, deal in zip(tabs, tab_order):
            with tab:
                st.markdown(
                    f"<div class='ll-md-deal-card'>{_pricing_block_html(deal, row)}</div>",
                    unsafe_allow_html=True,
                )
    with spec_col:
        vehicle_specs = [
            ("Condition", _fmt_or_dash(row.get("condition"))),
            ("Body type", _fmt_or_dash(row.get("body_type"))),
            ("Fuel", _fmt_or_dash(row.get("fuel_type"))),
            ("Transmission", _fmt_or_dash(row.get("transmission"))),
            ("Exterior", _fmt_or_dash(row.get("exterior_color"))),
            ("Interior", _fmt_or_dash(row.get("interior_color"))),
            ("Location", _fmt_or_dash(row.get("location"))),
            ("Dealer", _fmt_or_dash(row.get("dealer_name"))),
        ]
        rows_html = "".join(
            f"<div class='ll-md-spec-row'><span class='k'>{k}</span>"
            f"<span class='v'>{v}</span></div>"
            for k, v in vehicle_specs
        )
        st.markdown(
            f"<section class='ll-md-spec-card ll-md-spec-card--tall'>"
            f"<h4>{icon('info', 16, '#2E8BFF')} Vehicle & dealer</h4>"
            f"{rows_html}"
            f"</section>",
            unsafe_allow_html=True,
        )

    desc = _useful_description(row)
    if desc:
        st.markdown(
            f"<div class='ll-md-desc'>{desc}</div>",
            unsafe_allow_html=True,
        )

    # ---- Request CTA + form — single softer card instead of the heavy dark
    # navy banner, so it reads as the natural next step after the pricing tabs.
    st.markdown(
        f"<div class='ll-md-req-head'>"
        f"<div class='ll-md-req-ic'>{icon('phone', 18, '#2E8BFF')}</div>"
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
            label = f"{title_for(row)} ({featured})"
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
