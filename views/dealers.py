"""For Dealers — recruitment page pitching dealers on joining our network."""
from __future__ import annotations

import streamlit as st

from lib.icons import icon

# ---------------------------------------------------------------- hero panel
st.markdown(
    f"""
    <section class='ll-home-hero'>
      <div class='ll-hero-eyebrow'>{icon('star', 14, '#7aa9ff')} In-network dealer program</div>
      <h1>Sell more cars.<br/>Skip the marketing spend.</h1>
      <p>Join the All Cars Direct in-network dealer program and connect with
         pre-qualified, ready-to-buy customers who arrive at your lot with
         pricing already agreed. No haggling, no shoppers, no wasted hours
         on the floor.</p>
      <div class='ll-hero-ctas'>
        <a class='ll-hero-cta primary'
           href='mailto:info@allcarsdirectllc.com?subject=Dealer%20Application%20%E2%80%94%20Join%20In-Network%20Program'>
          Apply to join {icon('arrow-right', 16, '#ffffff')}
        </a>
        <a class='ll-hero-cta ghost' href='#why-join'>
          Why join
        </a>
      </div>
      <div class='ll-hero-trust'>
        <span>{icon('check-circle', 14, '#7aa9ff')} Pre-qualified leads</span>
        <span>{icon('tag', 14, '#7aa9ff')} No marketing spend</span>
        <span>{icon('key', 14, '#7aa9ff')} Faster deal velocity</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- why join
BENEFITS = [
    ("inbox", "Pre-qualified buyers",
     "Every customer that contacts you through All Cars Direct already knows "
     "the make, model, trim, and price. They're ready to sign — not to "
     "negotiate from scratch."),
    ("dollar-sign", "Zero customer acquisition cost",
     "We bring the customer to you. No SEM, no third-party lead resale, no "
     "lead-aggregator fees per deal. Your only investment is the pricing "
     "you set with us up front."),
    ("percent", "You set the price",
     "We never undercut you. You provide the floor pricing once; we present "
     "it to qualified buyers and the deal closes at your number. Volume "
     "comes from velocity, not from margin sacrifice."),
    ("layers", "Featured placement",
     "Active in-network dealers get priority placement on the storefront "
     "(homepage Top Deals, brand-tile featured slots, and search rankings). "
     "More eyeballs without an ad budget."),
    ("car", "Sign and Drive ready",
     "Our white-glove remote signing + nationwide delivery service expands "
     "your reach beyond your local market. Sell to a customer 1,000 miles "
     "away without a transporter call."),
    ("phone", "Direct line, real humans",
     "When you join the network, you get a single point of contact on our "
     "side. Quick deal questions, edge cases, escalations — all handled "
     "by name, not by ticket queue."),
]
benefits_html = ""
for i, (ic, title, body) in enumerate(BENEFITS, start=1):
    benefits_html += (
        f"<div class='ll-hiw-step'>"
        f"<div class='ll-hiw-num'>{i:02d}</div>"
        f"<div class='ll-hiw-ic'>{icon(ic, 22, '#7aa9ff')}</div>"
        f"<div class='ll-hiw-t'>{title}</div>"
        f"<div class='ll-hiw-d'>{body}</div>"
        f"</div>"
    )

st.markdown(
    f"""
    <a id='why-join'></a>
    <section class='ll-hiw-panel'>
      <div class='ll-hiw-eyebrow'>{icon('star', 14, '#7aa9ff')} Why dealers join</div>
      <h2>Built around dealer economics</h2>
      <p>Every part of the program is designed so you sell more cars with
         less overhead — not the other way around.</p>
      <div class='ll-hiw'>{benefits_html}</div>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- how-it-works
PROCESS = [
    ("file-text", "Apply to join",
     "Email us your dealer name, location, and a couple of contacts. We "
     "review your inventory mix and reputation, and schedule a 20-minute "
     "intro call."),
    ("percent", "Set your in-network pricing",
     "We work with you to set transparent below-MSRP pricing on the trims "
     "you want featured. You stay in control; we handle the customer-facing "
     "framing."),
    ("inbox", "Receive ready-to-close buyers",
     "Customers reach out through our Request a Deal flow. Your contact gets "
     "the lead, the agreed price, and a customer ready to sign. Close the "
     "deal, deliver the car, get paid."),
]
process_html = ""
for i, (ic, title, body) in enumerate(PROCESS, start=1):
    process_html += (
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
      <div class='ll-hiw-eyebrow'>{icon('route', 14, '#7aa9ff')} The three-step onboarding</div>
      <h2>From application to first sale in under two weeks</h2>
      <p>No long contracts, no setup fees, no SaaS subscription.</p>
      <div class='ll-hiw'>{process_html}</div>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- who we work with
st.markdown(
    f"""
    <section class='ll-why'>
      <div class='ll-why-ic'>{icon('info', 22, '#2E8BFF')}</div>
      <h2>Who we work with</h2>
      <p>We're selective. The in-network program is for dealers with
         <strong>strong CSI scores</strong>, <strong>transparent pricing
         practices</strong>, and the inventory depth to support reliable
         delivery. Both franchise and reputable independent dealers welcome.</p>
      <p style='margin-top: 14px;'>Right now we're actively growing in
         <strong>Florida, Texas, California, and the Northeast corridor</strong>
         — but apply from anywhere; we expand based on demand.</p>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- bottom CTA
st.markdown(
    f"""
    <section class='ll-hiw-cta'>
      <h2>Ready to join the network?</h2>
      <p>Email <strong>info@allcarsdirectllc.com</strong> with your dealership
         name and location — we'll be in touch within one business day.</p>
      <a class='ll-hero-cta primary'
         href='mailto:info@allcarsdirectllc.com?subject=Dealer%20Application%20%E2%80%94%20Join%20In-Network%20Program'>
        Apply to join {icon('arrow-right', 16, '#ffffff')}
      </a>
    </section>
    """,
    unsafe_allow_html=True,
)
