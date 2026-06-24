"""How It Works — concierge-negotiator explainer (matches home-hero design)."""
from __future__ import annotations

import streamlit as st

from lib.icons import icon

# ---------------------------------------------------------------- hero panel
st.markdown(
    f"""
    <section class='ll-home-hero'>
      <div class='ll-hero-eyebrow'>{icon('route', 14, '#7aa9ff')} The All Cars Direct playbook</div>
      <h1>How it works</h1>
      <p>We work directly with a vetted, in-network group of dealers across the
         country — locking in below-invoice pricing the average buyer could
         never get on their own. Tell us what you want and we'll do the rest.</p>
      <div class='ll-hero-ctas'>
        <a class='ll-hero-cta primary' href='/deals' target='_self'>
          Browse all deals {icon('arrow-right', 16, '#ffffff')}
        </a>
        <a class='ll-hero-cta ghost' href='mailto:info@allcarsdirectllc.com'>
          Talk to a specialist
        </a>
      </div>
      <div class='ll-hero-trust'>
        <span>{icon('check-circle', 14, '#7aa9ff')} In-network dealers only</span>
        <span>{icon('tag', 14, '#7aa9ff')} Below-invoice pricing</span>
        <span>{icon('key', 14, '#7aa9ff')} Pickup or delivery</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- steps panel
STEPS = [
    ("search", "Tell us what you want",
     "Browse our in-network pre-negotiated deals — or tell us the exact "
     "make, model, trim, and color you're after, even if it's not on the "
     "listings page. We track it down for you."),
    ("percent", "We negotiate. You get the price.",
     "We lock in real, below-invoice pricing the average buyer never sees, "
     "powered by direct relationships with our dealer network. You get "
     "transparent quotes via call, text, or email — no haggling, no "
     "showroom pressure, no surprise fees."),
    ("key", "Pick it up — or have it delivered",
     "Sign at the dealer and drive home, or skip the showroom entirely with "
     "our Sign and Drive remote-signing + white-glove delivery service "
     "(details below)."),
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
      <div class='ll-hiw-eyebrow'>{icon('layers', 14, '#7aa9ff')} The three-step process</div>
      <h2>From your shortlist to your driveway</h2>
      <p>Every step is designed to remove the games and put the numbers first.</p>
      <div class='ll-hiw'>{steps_html}</div>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- sign & drive
st.markdown(
    f"""
    <section class='ll-why'>
      <div class='ll-why-ic'>{icon('car', 22, '#2E8BFF')}</div>
      <h2>Sign and Drive — never visit a dealership</h2>
      <p>Our premium <strong>Sign and Drive</strong> service handles every
         step from your couch: remote document signing, all financing
         paperwork, and white-glove delivery straight to your driveway.
         Available on most in-network vehicles.</p>
      <p style='margin-top: 14px; font-weight: 600; color: var(--ll-ink);'>
        Interested? Email
        <a href='mailto:info@allcarsdirectllc.com?subject=Sign%20and%20Drive%20Inquiry'
           style='color:var(--ll-primary);text-decoration:none;'>
          info@allcarsdirectllc.com</a>
        to discuss your Sign and Drive deal.
      </p>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- bottom CTA
st.markdown(
    f"""
    <section class='ll-hiw-cta'>
      <h2>Ready to find your deal?</h2>
      <p>Browse our pre-negotiated offers, or tell us what you're looking for.</p>
      <a class='ll-hero-cta primary' href='/deals' target='_self'>
        Browse all deals {icon('arrow-right', 16, '#ffffff')}
      </a>
    </section>
    """,
    unsafe_allow_html=True,
)
