"""Landing page: hero, body-style tiles, top deals, how-it-works strip."""
from __future__ import annotations

from urllib.parse import quote_plus

import streamlit as st

from lib import db, scoring
from lib.deal_detail import show_detail
from lib.icons import body_icon_html, icon, make_icon_html
from lib.ui import card_html

# Force navigation in the top frame so Streamlit Cloud's iframe wrapper
# updates the visible URL in the same tab. Rendered as ``<span role=link>``
# (not ``<a>``) so Streamlit doesn't silently add target=_blank. See
# lib/styles.py top_nav for the full explanation.
NAV_GO = (
    "var u=this.dataset.href;"
    "try{(window.top||window).location.href=u;}"
    "catch(e){window.location.href=u;}"
)

# Toast confirming a just-submitted deal request (set inside the detail dialog).
if "req_toast" in st.session_state:
    st.toast(st.session_state.pop("req_toast"), icon=":material/check_circle:")

# ---------------------------------------------------------------- data
df = scoring.enrich(db.fetch_df(active_only=True))
active_deals = len(df)


# ---------------------------------------------------------------- hero
st.markdown(
    f"""
    <section class='ll-home-hero'>
      <div class='ll-hero-eyebrow'>{icon('bolt', 14, '#7aa9ff')} Pre-negotiated by our team</div>
      <h1>Smarter car deals.<br/>No haggling, no surprises.</h1>
      <p>Browse {active_deals or 'hundreds of'} curated lease, finance, and cash offers
         from trusted dealers. Compare side-by-side. Lock in pricing in minutes.</p>
      <div class='ll-hero-ctas'>
        <span class='ll-hero-cta primary' role='link' tabindex='0'
              data-href='/deals' onclick="{NAV_GO}">
          Browse all deals {icon('arrow-right', 16, '#ffffff')}
        </span>
      </div>
      <div class='ll-hero-trust'>
        <span>{icon('check-circle', 14, '#7aa9ff')} Verified dealers</span>
        <span>{icon('tag', 14, '#7aa9ff')} Pre-negotiated prices</span>
        <span>{icon('key', 14, '#7aa9ff')} Pickup or delivery</span>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------- body tiles
st.markdown("<h2 class='ll-home-h'>Shop by body style</h2>", unsafe_allow_html=True)

body_counts = (df["body_type"].dropna().value_counts().to_dict() if not df.empty else {})

# Canonical tile order (preferred), then alphabetical for anything else present.
PREFERRED = ["SUV", "Sedan", "Truck", "Coupe", "Convertible",
             "Hatchback", "Wagon", "Minivan"]
present = [b for b in PREFERRED if body_counts.get(b)]
present += sorted(b for b in body_counts if b not in PREFERRED and body_counts[b])

tiles = []
for b in present:
    tiles.append({
        "label": b, "count": body_counts.get(b, 0),
        "icon_html": body_icon_html(b, size=64),
        "href": f"/deals?body={quote_plus(b)}",
    })

if tiles:
    html = "<div class='ll-tiles'>"
    for t in tiles:
        html += (
            f"<span class='ll-tile' role='link' tabindex='0' "
            f"data-href='{t['href']}' onclick='{NAV_GO}'>"
            f"<div class='ll-tile-ic'>{t['icon_html']}</div>"
            f"<div class='ll-tile-lab'>{t['label']}</div>"
            f"<div class='ll-tile-ct'>{t['count']} deal{'s' if t['count'] != 1 else ''}</div>"
            f"</span>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
else:
    st.info("No active inventory yet — add a source on the Admin → Sources page.")


# ---------------------------------------------------------------- top deals
st.markdown("<h2 class='ll-home-h'>Top deals this week</h2>", unsafe_allow_html=True)

if not df.empty:
    top = df.copy()
    if "featured" in top.columns:
        top["_feat"] = top["featured"].fillna(0).astype(int)
    else:
        top["_feat"] = 0
    if "deal_score" in top.columns:
        top = top.sort_values(["_feat", "deal_score"], ascending=[False, False])
    else:
        top = top.sort_values("_feat", ascending=False)
    top = top.head(4)

    with st.container(key="home_top_deals"):
        cols = st.columns(min(4, len(top)), gap="small")
        for col, (_, row) in zip(cols, top.iterrows()):
            with col:
                with st.container(border=True, key=f"home_cardwrap_{row['id']}"):
                    st.markdown(card_html(row), unsafe_allow_html=True)
                    if st.button("View details",
                                 key=f"home_detail_{row['id']}",
                                 width="stretch", type="primary"):
                        show_detail(row.to_dict())

    ll_browse = st.columns([1, 2, 1])[1]
    with ll_browse:
        if st.button("Browse all deals", type="primary",
                     icon=":material/arrow_forward:", width="stretch",
                     key="home_browse_all"):
            st.switch_page("views/browse.py")
else:
    st.info("No deals yet. The crawler will populate them once a source is added.")


# ---------------------------------------------------------------- shop by make
make_counts = (df["make"].dropna().value_counts().to_dict() if not df.empty else {})
if make_counts:
    st.markdown("<h2 class='ll-home-h'>Shop by make</h2>", unsafe_allow_html=True)
    # Show every brand we have stock for, ordered by count then name.
    makes_sorted = sorted(make_counts.items(), key=lambda kv: (-kv[1], kv[0]))
    tiles_html = "<div class='ll-tiles ll-tiles-make'>"
    for make_name, count in makes_sorted:
        logo = make_icon_html(make_name, size=56, align="center")
        # Fallback for brands without a bundled logo — first 1-2 letters in a
        # circle, so the tile still reads as a brand marker.
        if not logo:
            initials = "".join(w[0] for w in make_name.split()[:2]).upper()
            logo = (
                f"<div style='width:56px;height:56px;border-radius:50%;"
                f"background:#eef2f8;color:#0E2A47;display:flex;align-items:center;"
                f"justify-content:center;font-weight:800;font-size:18px;'>"
                f"{initials}</div>"
            )
        tiles_html += (
            f"<span class='ll-tile' role='link' tabindex='0' "
            f"data-href='/deals?make={quote_plus(make_name)}' onclick='{NAV_GO}'>"
            f"<div class='ll-tile-ic'>{logo}</div>"
            f"<div class='ll-tile-lab'>{make_name}</div>"
            f"<div class='ll-tile-ct'>{count} deal{'s' if count != 1 else ''}</div>"
            f"</a>"
        )
    tiles_html += "</div>"
    st.markdown(tiles_html, unsafe_allow_html=True)


# ---------------------------------------------------------------- how it works
steps = [
    ("search", "Browse curated deals",
     "Filter by make, body, price, fuel, and term. Every deal is pre-negotiated."),
    ("file-text", "Request the deal",
     "Send your details — a specialist confirms availability and locks pricing."),
    ("car", "Drive away",
     "Pick up at the dealer or have it delivered. No haggling, no surprises."),
]
steps_html = ""
for i, (ic, t, d) in enumerate(steps, start=1):
    steps_html += (
        f"<div class='ll-hiw-step'>"
        f"<div class='ll-hiw-num'>{i:02d}</div>"
        f"<div class='ll-hiw-ic'>{icon(ic, 22, '#7aa9ff')}</div>"
        f"<div class='ll-hiw-t'>{t}</div>"
        f"<div class='ll-hiw-d'>{d}</div>"
        f"</div>"
    )
st.markdown(
    f"""
    <section class='ll-hiw-panel'>
      <div class='ll-hiw-eyebrow'>{icon('route', 14, '#7aa9ff')} A simple three-step process</div>
      <h2>How it works</h2>
      <p>From browsing to driving in under a week — without setting foot on a dealer lot.</p>
      <div class='ll-hiw'>{steps_html}</div>
    </section>
    """,
    unsafe_allow_html=True,
)
