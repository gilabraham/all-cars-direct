"""How It Works — customer-facing explainer page (matches home-hero design)."""
from __future__ import annotations

import streamlit as st

from lib.icons import icon

# Span-based nav so Streamlit doesn't silently add target=_blank to <a>
# tags. See lib/styles.py top_nav for the full explanation.
NAV_GO = (
    "var u=this.dataset.href;"
    "try{(window.top||window).location.href=u;}"
    "catch(e){window.location.href=u;}"
)


# ---------------------------------------------------------------- hero panel
st.markdown(
    f"""
    <section class='ll-home-hero'>
      <div class='ll-hero-eyebrow'>{icon('route', 14, '#7aa9ff')} The All Cars Direct playbook</div>
      <h1>How it works</h1>
      <p>From browsing to driving in under a week. Four simple steps, zero
         haggling, and complete number transparency the whole way through.</p>
      <div class='ll-hero-ctas'>
        <span class='ll-hero-cta primary' role='link' tabindex='0'
              data-href='/deals' onclick="{NAV_GO}">
          Browse all deals {icon('arrow-right', 16, '#ffffff')}
        </span>
        <a class='ll-hero-cta ghost' href='mailto:info@allcarsdirectllc.com'>
          Talk to a specialist
        </a>
      </div>
      <div class='ll-hero-trust'>
        <span>{icon('check-circle', 14, '#7aa9ff')} Pre-negotiated pricing</span>
        <span>{icon('tag', 14, '#7aa9ff')} Transparent math</span>
        <span>{icon('key', 14, '#7aa9ff')} Pickup or delivery</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- steps panel
STEPS = [
    ("search", "Browse curated deals",
     "Every listing is a real, pre-vetted lease, finance, or cash offer with "
     "fully transparent numbers — no asterisks, no surprise fees."),
    ("percent", "Compare the math",
     "We surface the effective monthly cost and % of MSRP so you can spot a "
     "genuinely strong deal — not just a low headline payment."),
    ("file-text", "Request your deal",
     "Found one you like? Send a request and we connect you with the dealer "
     "who has already agreed to the terms."),
    ("key", "Drive away",
     "No back-and-forth haggling. Sign at the price you saw and pick up your "
     "car — or have it delivered to your door."),
]
steps_html = ""
for i, (ic, title, body) in enumerate(STEPS, start=1):
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
      <div class='ll-hiw-eyebrow'>{icon('layers', 14, '#7aa9ff')} The four steps</div>
      <h2>A faster way to a better deal</h2>
      <p>Every step is designed to put the numbers first and the dealer pressure last.</p>
      <div class='ll-hiw'>{steps_html}</div>
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
      <span class='ll-hero-cta primary' role='link' tabindex='0'
            data-href='/deals' onclick="{NAV_GO}">
        Browse all deals {icon('arrow-right', 16, '#ffffff')}
      </span>
    </section>
    """,
    unsafe_allow_html=True,
)
