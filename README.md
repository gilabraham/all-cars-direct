# All Cars Direct

A car **lease / finance / cash** broker marketplace built with [Streamlit](https://streamlit.io).
Customers browse curated, pre-negotiated deals; admins manage inventory, monitor requests,
and (optionally) pull inventory from dealer sites via the built-in web crawler.

Live deploy target: Streamlit Community Cloud → CNAME to GoDaddy domain.

## Features

**Customer storefront**
- **Home** — hero, Shop-by-body-style + Shop-by-make tile widgets, "Top deals this week",
  "How it works" panel
- **Deals** (`/deals`) — left-rail filter (or mobile flyout) for deal type, price, make, model,
  body, fuel, year, featured-only; full-text search; sort by featured / deal-score /
  monthly / effective monthly / % of MSRP / newest / make
- **Per-deal modal** — image card, deal-type + rating chips, big price block,
  pricing / terms / vehicle spec cards, and a "Request this deal" form
- **How it works** + **About** pages — dark-panel design system, mobile-responsive
- **URL state** — filter selections sync to the URL so refresh / copy-paste preserves state

**Admin back-office** (password-gated)
- **Dashboard** — live KPIs and charts
- **Manage Listings** — inline spreadsheet editor + add / edit / delete forms
- **Requests** — inbound deal-request management (status, notes, customer contact)
- **Bulk CSV Upload** — template + sample download, validation, preview, append or replace
- **Sources** — register URLs for the crawler to pull inventory from (currently disabled
  via `CRAWLER_ENABLED` flag in `lib/auth.py` — flip to `True` to re-enable)

## Quick start (local dev)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml — set a strong admin_password

streamlit run streamlit_app.py
```

The app opens at <http://localhost:8530> (port set in `.streamlit/config.toml`).
On first run, 40 sample listings are seeded into `data/deals.db` (gitignored).

## Deploy to Streamlit Community Cloud

1. **Push to GitHub** (public repo).
2. Sign in to <https://share.streamlit.io> with GitHub → *New app*.
3. Select repo, branch, and `streamlit_app.py` as the entry point.
4. **Settings → Secrets** — paste:
   ```toml
   admin_password = "your-strong-production-password"
   # Optional SMTP keys — see .streamlit/secrets.toml.example
   ```
5. Deploy. App goes live at `https://<your-app>.streamlit.app`.

**Custom domain (GoDaddy):**
- In GoDaddy DNS, add a CNAME: `www` → `<your-app>.streamlit.app` (TTL 600).
- *My Products → Domain → Forwarding* → forward apex `allcarsdirectllc.com` →
  `https://www.allcarsdirectllc.com` (permanent 301, masking off).
- DNS propagation: 10 minutes to a few hours.

> **Heads-up:** SQLite on Streamlit Cloud is **ephemeral** — every redeploy wipes
> `data/deals.db`. Fine for the placeholder seed; for real customer data, migrate to
> Postgres (Streamlit Connections) or move to a host with a persistent disk
> (Render / Railway / Fly.io).

## Admin access

After deploying, visit `/admin` (or any `/admin-*` page) → enter the password set in
secrets. Append `?logout=1` to any URL to clear the session.

## CSV format

Required columns: `make`, `model`, `year`. All others are optional. Grab a starter file
from **Bulk CSV Upload → Download blank template**. Recognized columns:

```
make, model, year, trim, body_type, deal_type, fuel_type,
monthly_payment, down_payment, term_months, annual_mileage,
msrp, selling_price, money_factor, residual_percent,
exterior_color, location, dealer_name, image_url, description,
featured, status
```

`deal_type` is one of `Lease`, `Finance`, `Cash`. Unknown columns are ignored;
invalid rows are reported and skipped.

## Project layout

```
streamlit_app.py        # entry point + navigation
lib/
  auth.py               # admin password gate + CRAWLER_ENABLED flag
  crawler/              # web crawler (generic + selector parsers)
  db.py                 # SQLite data layer
  deal_detail.py        # shared deal-details modal (browse + home top-deals)
  icons.py              # inline SVG icons + body silhouettes + brand logos
  images.py             # imagin.studio CDN + offline SVG fallback
  mailer.py             # SMTP "Request this deal" emails
  scoring.py            # deal metrics + 0–100 score / rating
  seed.py               # sample inventory + CSV template/sample export
  styles.py             # shared CSS + nav / hero helpers + admin sub-nav
  ui.py                 # formatting + HTML deal cards
views/
  home.py               # landing page
  browse.py             # /deals — customer deal browser
  how_it_works.py       # /how-it-works
  about.py              # /about
  dashboard.py          # /admin
  manage.py             # /admin-listings
  requests.py           # /admin-requests
  upload.py             # /admin-upload
  sources.py            # /admin-sources (crawler URLs)
assets/                  # logos, body-type slices, brand SVGs
data/                    # SQLite db (gitignored)
scripts/                 # slice_body_sprite.py and other one-shot utilities
```

## Notes

- **Deal scoring** is based on the "1% rule" — effective monthly at or below ~1% of
  MSRP is a strong lease.
- **Body-type icons** are pre-sliced from `assets/bodyType.png` by
  `scripts/slice_body_sprite.py`. Drop in `.webp` files at `assets/body-types/<name>.webp`
  to override.
- **Brand logos** come from [cardog-ai/icons](https://github.com/cardog-ai/icons)
  (MIT). Add more by dropping `<brand-slug>.svg` into `assets/car-logos/`.
- **Web crawler** is disabled by default (`CRAWLER_ENABLED=False` in `lib/auth.py`)
  so the admin can preview the UI without live crawling. Flip to `True` to enable.
