"""About All Cars Direct — matches the home / how-it-works design system."""
from __future__ import annotations

import streamlit as st

from lib import db, scoring
from lib.icons import icon

# Force top-frame navigation so Streamlit Cloud's iframe wrapper updates the
# visible URL in the same tab. See lib/styles.py top_nav for details.
NAV_ONCLICK = "if(window.top){window.top.location.href=this.href;return false;}"


# ---------------------------------------------------------------- live snapshot
adf = scoring.enrich(db.fetch_df(active_only=True))
live_deals = len(adf)
brand_count = adf["make"].nunique() if not adf.empty else 0
lease_count = int((adf["deal_type"] == "Lease").sum()) if not adf.empty else 0
disc = adf["discount_percent"].dropna() if "discount_percent" in adf.columns else None
avg_disc = (f"{disc.mean():.1f}%" if disc is not None and not disc.empty else "—")


# ---------------------------------------------------------------- hero panel
st.markdown(
    f"""
    <section class='ll-home-hero'>
      <div class='ll-hero-eyebrow'>{icon('info', 14, '#7aa9ff')} Our story</div>
      <h1>Smarter car deals.<br/>Minus the games.</h1>
      <p>All Cars Direct exists to take the guesswork and gamesmanship out of
         getting a car. We surface curated lease, finance, and cash offers —
         and show the full math behind every single one.</p>
      <div class='ll-hero-ctas'>
        <a class='ll-hero-cta primary' href='/deals' onclick="{NAV_ONCLICK}">
          Browse all deals {icon('arrow-right', 16, '#ffffff')}
        </a>
        <a class='ll-hero-cta ghost' href='mailto:info@allcarsdirectllc.com' onclick="{NAV_ONCLICK}">
          Talk to a specialist
        </a>
      </div>
      <div class='ll-hero-trust'>
        <span>{icon('check-circle', 14, '#7aa9ff')} Verified dealers</span>
        <span>{icon('tag', 14, '#7aa9ff')} Transparent math</span>
        <span>{icon('key', 14, '#7aa9ff')} Pickup or delivery</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- live stats
if not adf.empty:
    st.markdown(
        f"""
        <section class='ll-about-stats'>
          <div class='ll-about-stat'>
            <div class='ll-about-stat-n'>{live_deals}</div>
            <div class='ll-about-stat-l'>Live deals</div>
          </div>
          <div class='ll-about-stat'>
            <div class='ll-about-stat-n'>{brand_count}</div>
            <div class='ll-about-stat-l'>Brands</div>
          </div>
          <div class='ll-about-stat'>
            <div class='ll-about-stat-n'>{lease_count}</div>
            <div class='ll-about-stat-l'>Lease offers</div>
          </div>
          <div class='ll-about-stat'>
            <div class='ll-about-stat-n'>{avg_disc}</div>
            <div class='ll-about-stat-l'>Avg discount</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------- value props
PROPS = [
    ("search", "Full transparency",
     "Effective monthly, money factor, residual, and discount — shown on every "
     "single deal so you know exactly what you're paying."),
    ("check-circle", "Pre-negotiated",
     "Each listing is a real offer a dealer has already agreed to. "
     "No bait-and-switch, no surprise fees at signing."),
    ("layers", "Every way to buy",
     "Lease, finance, or cash — compare them side by side and pick the "
     "structure that actually fits your situation."),
    ("map-pin", "Nationwide network",
     "Deals from trusted dealers across the country, many of whom ship "
     "nationwide — pick up locally or have it delivered."),
]
steps_html = ""
for i, (ic, title, body) in enumerate(PROPS, start=1):
    steps_html += (
        f"<div class='ll-hiw-step'>"
        f"<div class='ll-hiw-num'>{i:02d}</div>"
        f"<div class='ll-hiw-ic'>{icon(ic, 22, '#7aa9ff')}</div>"
        f"<div class='ll-hiw-t'>{title}</div>"
        f"<div class='ll-hiw-d'>{body}</div>"
        f"</div>"
    )
st.markdown(
    f"""
    <section class='ll-hiw-panel'>
      <div class='ll-hiw-eyebrow'>{icon('star', 14, '#7aa9ff')} What makes us different</div>
      <h2>Built around the numbers, not the noise</h2>
      <p>Four things every customer gets — every time, on every deal.</p>
      <div class='ll-hiw'>{steps_html}</div>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- contact card
st.markdown(
    f"""
    <section class='ll-why'>
      <div class='ll-why-ic'>{icon('phone', 22, '#2E8BFF')}</div>
      <h2>Get in touch</h2>
      <p>Questions, or a specific car in mind? Reach us at
         <strong><a href='mailto:info@allcarsdirectllc.com'
                   style='color:var(--ll-primary);text-decoration:none'>
         info@allcarsdirectllc.com</a></strong> — or browse what's available
         right now.</p>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- bottom CTA
st.markdown(
    f"""
    <section class='ll-hiw-cta'>
      <h2>Ready to find your deal?</h2>
      <p>Browse hundreds of pre-negotiated offers from trusted dealers.</p>
      <a class='ll-hero-cta primary' href='/deals' onclick="{NAV_ONCLICK}">
        Browse all deals {icon('arrow-right', 16, '#ffffff')}
      </a>
    </section>
    """,
    unsafe_allow_html=True,
)
