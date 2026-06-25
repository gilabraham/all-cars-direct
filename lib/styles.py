"""Shared CSS + small HTML helpers for a slick, modern look."""
from __future__ import annotations

import functools
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"


@functools.lru_cache(maxsize=None)
def brand_svg(name: str) -> str:
    """Return the raw markup of a brand SVG from /assets (empty if missing)."""
    try:
        return (ASSETS / name).read_text()
    except OSError:
        return ""


CSS = """
<style>
:root {
  --ll-bg: #ffffff;
  --ll-card: #ffffff;
  --ll-border: #e7eaf3;
  --ll-muted: #6b7280;
  --ll-ink: #1c2333;
  --ll-primary: #2E8BFF;
  --ll-navy: #0E2A47;
}

/* Hide Streamlit's default top chrome so our nav can sit flush */
[data-testid="stHeader"] { display: none; }

/* While Streamlit reruns it fades "stale" element containers to ~0.6 opacity.
   That made the fixed nav briefly see-through on every button click. Scope the
   override to only the nav's container so other elements (e.g. the BaseWeb
   selectbox popover) can fade/close cleanly. */
[data-testid="stElementContainer"]:has(.ll-nav-wrap),
[data-testid="stElementContainer"]:has(.ll-nav-wrap)[data-stale="true"] {
  opacity: 1 !important;
}
/* Disable the native sidebar collapse control — the in-page "Filters & sort"
   toggle controls the panel instead (the native expand button lived in the
   hidden header, which left no way to reopen a collapsed sidebar). */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none !important; }

/* Wider content area + room for the fixed full-width nav, with tighter
   horizontal page padding (Carvana-style edge-to-edge feel). */
.block-container {
  padding-top: 92px !important; padding-bottom: 3rem;
  padding-left: 24px !important; padding-right: 24px !important;
  max-width: 1600px;
}
/* Prevent any oversized content (wide grids, etc.) from forcing the whole
   page to scroll horizontally on mobile. */
html, body, [data-testid="stAppViewContainer"] { overflow-x: hidden; }
@media (max-width: 880px) {
  .block-container {
    padding-top: 76px !important;            /* shorter mobile nav */
    padding-left: 14px !important;
    padding-right: 14px !important;
  }
}
@media (max-width: 540px) {
  .block-container { padding-left: 10px !important; padding-right: 10px !important; }
}
/* Push sidebar content below the fixed nav */
section[data-testid="stSidebar"] { padding-top: 80px; }

/* ---- Top navigation header (Carvana-style light) ---- */
.ll-nav-wrap {
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000001;
  background: #ffffff;
  border-bottom: 1px solid var(--ll-border);
  box-shadow: 0 1px 2px rgba(15,23,42,0.04), 0 4px 18px -10px rgba(15,23,42,0.12);
  transform: translateZ(0); backface-visibility: hidden; will-change: transform;
}
.ll-nav {
  display: flex; align-items: center; gap: 18px;
  height: 70px; max-width: 1600px; margin: 0 auto; padding: 0 28px;
}
.ll-brand-link { display: flex; align-items: center; text-decoration: none; flex-shrink: 0;
  cursor: pointer; user-select: none; }
.ll-brand-link svg { height: 46px; width: auto; display: block; }
.ll-brand-link span { color: var(--ll-navy) !important; font-weight: 800; font-size: 20px; letter-spacing: 1px; }
.ll-nav-right { display: flex; align-items: center; gap: 4px; margin-left: auto; }
.ll-navlinks { display: flex; align-items: center; gap: 2px; }
/* Override Streamlit's theme link color and style nav links Carvana-style
   (dark text on white, with a blue underline on the active link). */
.ll-nav .ll-navlink,
.ll-nav .ll-navlink:link,
.ll-nav .ll-navlink:visited {
  color: var(--ll-ink) !important; text-decoration: none !important;
  font-weight: 500; font-size: 14.5px; letter-spacing: 0.1px;
  height: 70px; display: flex; align-items: center;
  padding: 0 14px; border-bottom: 3px solid transparent;
  transition: color .15s, border-color .15s; white-space: nowrap;
  cursor: pointer; user-select: none;
}
.ll-nav .ll-navlink:hover { color: var(--ll-primary) !important; }
.ll-nav .ll-navlink.active {
  color: var(--ll-primary) !important; border-bottom-color: var(--ll-primary);
}
.ll-nav-cta, .ll-nav-cta:link, .ll-nav-cta:visited {
  background: var(--ll-primary); color: #fff !important; text-decoration: none !important;
  font-weight: 700; font-size: 14px; padding: 10px 20px; border-radius: 999px;
  margin-left: 10px; white-space: nowrap; transition: background .15s;
}
.ll-nav-cta:hover { background: #1e6fd0; }

/* ===== Mobile nav: compact, horizontally-scrollable links, smaller CTA ===== */
@media (max-width: 880px) {
  .ll-nav {
    height: 60px; padding: 0 14px; gap: 10px;
    max-width: 100%; overflow: hidden;
  }
  .ll-brand-link svg { height: 36px; }
  .ll-brand-link span { font-size: 16px; letter-spacing: 0.5px; }
  .ll-nav-right { gap: 0; flex: 1 1 auto; min-width: 0;
    justify-content: flex-end; }
  /* Horizontally scrollable nav links — fits any number of items on any
     viewport without cutting them off. The scroll bar is hidden visually. */
  .ll-navlinks {
    flex: 1 1 auto; min-width: 0; max-width: 100%;
    overflow-x: auto; overflow-y: hidden;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    margin-right: 6px;
  }
  .ll-navlinks::-webkit-scrollbar { display: none; }
  .ll-nav .ll-navlink {
    height: 60px; padding: 0 10px;
    font-size: 13px; flex: 0 0 auto;
    border-bottom-width: 3px;
  }
  .ll-nav-cta {
    margin-left: 0; padding: 7px 14px; font-size: 13px;
    flex-shrink: 0;
  }
}
@media (max-width: 540px) {
  .ll-nav { padding: 0 10px; gap: 6px; }
  .ll-brand-link span { display: none; }   /* icon-only brand on the smallest screens */
  .ll-nav-cta { padding: 7px 12px; }
}

/* Admin sub-nav (only shown on admin pages) */
.ll-subnav { display:flex; align-items:center; gap:12px; background:#eef1f8;
  border:1px solid var(--ll-border); border-radius:12px; padding:8px 14px;
  margin: 0 0 18px; flex-wrap:wrap; }
.ll-subnav-label { font-size:11px; font-weight:800; letter-spacing:.9px; color:#9aa3b2;
  text-transform:uppercase; }
.ll-subnav nav { display:flex; gap:4px; flex-wrap:wrap; }
.ll-subnav .ll-subnavlink,
.ll-subnav .ll-subnavlink:link,
.ll-subnav .ll-subnavlink:visited {
  color: var(--ll-muted) !important; text-decoration:none !important; font-weight:650;
  font-size:13px; padding:6px 12px; border-radius:8px; text-transform:uppercase;
  letter-spacing:.4px; transition: color .15s, background .15s;
  cursor: pointer; user-select: none; }
.ll-subnav .ll-subnavlink:hover { color: var(--ll-ink) !important; background:#ffffff; }
.ll-subnav .ll-subnavlink.active { color:#fff !important; background:var(--ll-primary); }
.ll-subnav .ll-subnavlink.ll-logout { color:#dc2626 !important; }

/* Sidebar brand */
.ll-brand { display:flex; align-items:center; gap:8px; font-weight:800; font-size:18px;
  color:var(--ll-ink); padding:2px 0 8px 2px; }
.ll-brand span { letter-spacing:-0.3px; }

/* ---- Filter / sort panel ---- */
section[data-testid="stSidebar"] { border-right: 1px solid var(--ll-border); }
.ll-side-head { font-weight: 820; font-size: 19px; color: var(--ll-ink);
  letter-spacing: -0.3px; margin: 0 0 12px; }
.ll-side-sec { font-size: 11px; font-weight: 800; letter-spacing: 0.9px;
  text-transform: uppercase; color: #9aa3b2; margin: 18px 0 4px; }
/* Pills: rounded, brand-tinted when selected */
section[data-testid="stSidebar"] [data-testid="stPills"] button {
  border-radius: 999px !important; font-weight: 650 !important; }
/* Tighten control spacing for a denser, modern panel */
section[data-testid="stSidebar"] [data-testid="stSelectbox"],
section[data-testid="stSidebar"] [data-testid="stMultiSelect"],
section[data-testid="stSidebar"] [data-testid="stTextInput"],
section[data-testid="stSidebar"] [data-testid="stSlider"] { margin-bottom: 6px; }
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-testid="stTextInput"] input {
  border-radius: 10px; }

/* Brand header */
.ll-hero {
  background: linear-gradient(120deg, #0E2A47 0%, #1e5fa8 58%, #2E8BFF 100%);
  border-radius: 20px;
  padding: 28px 32px;
  color: #fff;
  margin-bottom: 8px;
  box-shadow: 0 18px 40px -18px rgba(14,42,71,0.6);
}
.ll-hero h1 { color:#fff; font-size: 36px; margin: 0; font-weight: 800; letter-spacing:-0.5px;}
.ll-hero p { color: rgba(255,255,255,0.92); margin: 7px 0 0 0; font-size: 16.5px; }
.ll-hero-top { display:flex; align-items:center; gap:13px; }
.ll-hero-ic { display:inline-flex; align-items:center; }
.ll-hero-ic svg { width:36px; height:36px; }

/* ---- Deal card (Carvana-style, slick) ----
   The visual frame (border, bg, shadow, hover lift) is provided by the
   st.container(border=True) wrapper [class*="cardwrap_"] so the
   "View details" button below the HTML reads as part of the same card. */
.ll-card {
  background: transparent;
  border: none;
  box-shadow: none;
  display: flex; flex-direction: column;
}

[class*="cardwrap_"] {
  padding: 0 !important;
  background: #ffffff !important;
  border: 1px solid var(--ll-border) !important;
  border-radius: 16px !important;
  overflow: hidden !important;
  box-shadow: 0 1px 2px rgba(15,23,42,0.04);
  transition: transform .18s ease, box-shadow .18s ease, border-color .15s;
  /* Stretch to the column's full height so every card in a row lines up. */
  height: 100%;
  display: flex; flex-direction: column;
}
[class*="cardwrap_"]:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 40px -22px rgba(15,23,42,0.30), 0 4px 12px -8px rgba(15,23,42,0.10);
  border-color: #d6dbe5;
}
[class*="cardwrap_"] > div[data-testid="stVerticalBlock"] {
  gap: 0 !important;
  flex: 1;                /* let the inner vertical block stretch... */
  display: flex; flex-direction: column;
}
/* ...so the markdown-rendered .ll-card can claim the remaining height
   and push the View-details button to the wrap's bottom edge. */
[class*="cardwrap_"] [data-testid="stMarkdown"] { flex: 1; display: flex; }
[class*="cardwrap_"] [data-testid="stMarkdown"] > div { flex: 1; display: flex; }
[class*="cardwrap_"] .ll-card { flex: 1; }
/* Streamlit's column container needs to opt into stretching its children. */
[data-testid="stColumn"] > div[data-testid="stVerticalBlock"] { height: 100%; }
/* The Details button becomes the card's bottom edge — square corners merging
   into the rounded container, full width, no extra margin. */
[class*="cardwrap_"] [data-testid="stButton"] { margin: 0 !important; }
[class*="cardwrap_"] [data-testid="stButton"] > button {
  border: none !important;
  border-top: 1px solid var(--ll-border) !important;
  border-radius: 0 !important;
  height: 48px;
  font-weight: 700 !important;
}

.ll-card-media { position: relative; aspect-ratio: 16/10; overflow: hidden;
  background: #eef2f8;
  display: flex; align-items: center; justify-content: center;
  padding: 8px;
}
/* ``contain`` so wide truck side-views and tall SUV 3/4 shots both show the
   whole vehicle. The card's light-blue tray reads as intentional letterbox. */
.ll-card-media img { max-width: 100%; max-height: 100%; width: auto; height: auto;
  object-fit: contain; display: block; transition: transform .35s ease; }
.ll-card:hover .ll-card-media img { transform: scale(1.03); }

/* Deal-type pills on the image (top-left). Single-row flex; tuned to fit
   three pills (LEASE / FINANCE / CASH) inside the narrower home-page card
   image without wrapping over the vehicle. */
.ll-card-types {
  position: absolute; top: 10px; left: 10px;
  display: inline-flex; gap: 4px;
  max-width: calc(100% - 52px);
}
.ll-card-type {
  font-size: 10px; font-weight: 750; letter-spacing: .35px; text-transform: uppercase;
  padding: 4px 9px; border-radius: 999px; color: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.18);
  white-space: nowrap; line-height: 1.2;
}
/* Non-featured pills sit slightly muted so the featured one still reads as
   the "primary" offer the card's price is showing. */
.ll-card-type.is-alt { opacity: 0.78; }
/* Featured star (top-right) */
.ll-card-fav {
  position: absolute; top: 11px; right: 11px;
  background: rgba(255,255,255,0.95); border-radius: 999px;
  padding: 5px 7px; display: inline-flex; align-items: center;
  box-shadow: 0 2px 6px rgba(0,0,0,0.14);
}

.ll-card-body { padding: 18px 20px 8px; flex: 1; }
.ll-card-title { font-size: 18.5px; font-weight: 760; color: var(--ll-ink);
  margin: 0 0 3px; line-height: 1.25; letter-spacing: -0.2px; }
.ll-card-sub { font-size: 13px; color: var(--ll-muted); margin: 0 0 14px; }

.ll-card-price { display: flex; align-items: baseline; gap: 6px; margin: 0 0 6px; }
.ll-card-amt {
  font-size: 30px; font-weight: 820; color: var(--ll-ink);
  letter-spacing: -0.6px; line-height: 1;
}
.ll-card-unit { font-size: 13px; font-weight: 600; color: var(--ll-muted); }
.ll-card-spec { font-size: 13px; color: var(--ll-muted); margin: 0 0 6px; }
.ll-card-alts {
  font-size: 12px; color: var(--ll-muted); font-weight: 600;
  margin: 2px 0 0; padding-top: 6px; border-top: 1px dashed var(--ll-border);
}

.ll-card-foot {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 20px 16px; border-top: 1px solid var(--ll-border); margin-top: 14px;
}
.ll-card-loc { font-size: 12.5px; color: var(--ll-muted);
  display: inline-flex; align-items: center; gap: 5px; }
.ll-card-rate { display: inline-flex; align-items: center; gap: 6px; }
.ll-card-rate .dot { width: 8px; height: 8px; border-radius: 50%; }
.ll-card-rate .lab { font-size: 12.5px; font-weight: 700; }

/* Stat strip */
.ll-stats { display:flex; gap:16px; flex-wrap:wrap; margin: 8px 0 20px 0;}
.ll-stat { background: var(--ll-card); border:1px solid var(--ll-border); border-radius:14px;
  padding:16px 22px; min-width:160px; flex:1; }
.ll-stat .n { font-size:28px; font-weight:820; color:var(--ll-ink); letter-spacing:-0.5px;}
.ll-stat .l { font-size:12.5px; color:var(--ll-muted); text-transform:uppercase; letter-spacing:.4px;}

.ll-detail-grid { display:grid; grid-template-columns: 1fr 1fr; gap: 11px 24px; margin-top:8px;}
.ll-detail-grid .k { font-size:12.5px; color:var(--ll-muted); text-transform:uppercase; letter-spacing:.3px;}
.ll-detail-grid .v { font-size:16px; color:var(--ll-ink); font-weight:680; }

/* ===================== Deal details modal ===================== */
/* Image card */
.ll-md-img {
  background: linear-gradient(180deg, #f6f8fb 0%, #eef2f8 100%);
  border-radius: 16px; padding: 14px; border: 1px solid var(--ll-border);
}
.ll-md-img img { border-radius: 10px; display: block; width: 100% !important; }

/* Photo gallery — horizontal scrollable thumbnail strip under the hero. */
.ll-md-thumbs {
  display: flex; gap: 8px; margin-top: 10px;
  overflow-x: auto; padding: 2px 2px 8px; scrollbar-width: thin;
}
.ll-md-thumbs::-webkit-scrollbar { height: 6px; }
.ll-md-thumbs::-webkit-scrollbar-thumb {
  background: #c9d2e0; border-radius: 999px;
}
.ll-md-thumb {
  flex: 0 0 auto; width: 72px; height: 56px;
  border: 1px solid var(--ll-border); border-radius: 8px;
  overflow: hidden; background: #eef2f8;
  transition: border-color .15s ease, transform .15s ease;
}
.ll-md-thumb:hover {
  border-color: var(--ll-primary); transform: translateY(-1px);
}
.ll-md-thumb img {
  width: 100%; height: 100%; object-fit: cover; display: block;
}

/* Chips row above the title in the right info column. */
.ll-md-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 10px; }
.ll-md-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 5px 12px; border-radius: 999px;
  font-size: 11.5px; font-weight: 750; letter-spacing: 0.35px;
  text-transform: uppercase; border: 1px solid transparent;
  line-height: 1.2;
}
.ll-md-chip svg { display: inline-block; }

/* Title + subtitle */
.ll-md-title {
  margin: 0 0 4px; font-size: 26px; font-weight: 820;
  color: var(--ll-ink); letter-spacing: -0.5px; line-height: 1.1;
}
.ll-md-sub {
  margin: 0 0 10px; color: #6b7686; font-size: 14px; line-height: 1.45;
}

/* Big price block */
.ll-md-price {
  margin: 0 0 14px; padding: 18px 20px;
  background: linear-gradient(135deg, #f6faff 0%, #eef4ff 100%);
  border: 1px solid #d8e6fb; border-radius: 14px;
}
.ll-md-price-row { display: flex; align-items: baseline; gap: 8px; }
.ll-md-price-amt {
  font-size: 36px; font-weight: 800; color: var(--ll-ink);
  letter-spacing: -1px; line-height: 1; font-feature-settings: 'tnum';
}
.ll-md-price-unit {
  font-size: 14px; font-weight: 600; color: #6b7686;
}
.ll-md-price-sub {
  margin-top: 8px; font-size: 13px; color: #5a6577;
  font-weight: 500;
}

/* Location row */
.ll-md-loc {
  display: flex; align-items: center; gap: 6px;
  font-size: 13.5px; color: #6b7686;
  margin: 0 0 6px;
}
.ll-md-loc svg { flex: 0 0 auto; }

/* Tabbed pricing card (Lease / Finance / Cash) inside the deal-details
   modal. Mirrors the Coral-Springs PDP: rounded segmented control on top
   showing the headline price per deal, a single deal's full breakdown
   below. Streamlit's stock tab strip is fully re-skinned. */
[role="dialog"] [data-testid="stTabs"] {
  margin-top: 18px;
}
[role="dialog"] [data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 8px; border-bottom: none; padding: 6px;
  background: #f1f4f9; border-radius: 14px;
  display: inline-flex; width: auto;
}
[role="dialog"] [data-testid="stTabs"] [data-baseweb="tab"] {
  border: none; border-radius: 10px;
  padding: 9px 18px; background: transparent; height: auto;
  font-size: 13px; font-weight: 700; color: #5a6577;
  letter-spacing: 0.2px;
  transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}
[role="dialog"] [data-testid="stTabs"] [data-baseweb="tab"]:hover {
  color: var(--ll-ink);
}
[role="dialog"] [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
  background: #ffffff; color: var(--ll-ink);
  box-shadow: 0 1px 3px rgba(14, 42, 71, 0.08),
              0 0 0 1px rgba(14, 42, 71, 0.06);
}
[role="dialog"] [data-testid="stTabs"] [data-baseweb="tab-highlight"],
[role="dialog"] [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }
[role="dialog"] [data-testid="stTabs"] [data-baseweb="tab-panel"] { padding-top: 14px; }

.ll-md-deal-card {
  margin: 4px 0; padding: 24px 26px;
  background: #ffffff;
  border: 1px solid #e4ebf3; border-radius: 16px;
  box-shadow: 0 1px 2px rgba(14, 42, 71, 0.04),
              0 8px 24px -12px rgba(14, 42, 71, 0.10);
}
.ll-md-deal-price {
  display: flex; align-items: baseline; gap: 10px;
  padding-bottom: 16px; margin-bottom: 14px;
  border-bottom: 1px solid #eef2f7;
}
.ll-md-deal-amt {
  font-size: 44px; font-weight: 820; color: var(--ll-ink);
  letter-spacing: -1.4px; line-height: 1; font-feature-settings: 'tnum';
}
.ll-md-deal-unit { font-size: 14.5px; font-weight: 650; color: #6b7686; }
.ll-md-deal-rows .ll-md-spec-row {
  padding: 8px 0; font-size: 14px;
  border-bottom: 1px dashed #eef2f7;
}
.ll-md-deal-rows .ll-md-spec-row:last-child { border-bottom: none; }

/* Spec grid: three grouped cards */
.ll-md-specs {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;
  margin: 22px 0 16px;
}
.ll-md-spec-card {
  background: #fff; border: 1px solid var(--ll-border); border-radius: 12px;
  padding: 14px 16px;
}
/* Vehicle & dealer — clean 2-column spec list, dashed dividers between
   rows so it reads like a proper spec sheet (label left, value right). */
.ll-md-vd-strip {
  margin: 22px 0 8px; padding: 20px 24px;
  background: #ffffff;
  border: 1px solid #e4ebf3; border-radius: 14px;
  box-shadow: 0 1px 2px rgba(14, 42, 71, 0.04),
              0 8px 24px -16px rgba(14, 42, 71, 0.10);
}
.ll-md-vd-strip h4 {
  display: flex; align-items: center; gap: 8px;
  margin: 0 0 8px; padding-bottom: 12px;
  border-bottom: 1px solid #eef2f7;
  font-size: 12px; font-weight: 750; color: var(--ll-ink);
  text-transform: uppercase; letter-spacing: 0.4px;
}
.ll-md-vd-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 36px;
}
.ll-md-vd-item {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 16px; padding: 10px 0; min-width: 0;
  border-bottom: 1px dashed #eef2f7;
}
/* Last item in each column has no underline. The grid lays out items in
   row-major order, so the last two visual items are the final children. */
.ll-md-vd-item:nth-last-child(-n + 2) { border-bottom: none; }
.ll-md-vd-item .k {
  font-size: 13.5px; color: #6b7686; font-weight: 500;
  flex-shrink: 0;
}
.ll-md-vd-item .v {
  font-size: 14px; font-weight: 700; color: var(--ll-ink);
  font-feature-settings: 'tnum';
  text-align: right;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  min-width: 0;
}
@media (max-width: 720px) {
  .ll-md-vd-grid { grid-template-columns: 1fr; column-gap: 0; }
  .ll-md-vd-item:nth-last-child(-n + 2) { border-bottom: 1px dashed #eef2f7; }
  .ll-md-vd-item:last-child { border-bottom: none; }
}
.ll-md-spec-card h4 {
  display: flex; align-items: center; gap: 8px;
  margin: 0 0 10px; padding-bottom: 8px;
  border-bottom: 1px solid var(--ll-border);
  font-size: 12px; font-weight: 750; color: var(--ll-ink);
  text-transform: uppercase; letter-spacing: 0.4px;
}
.ll-md-spec-row {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 5px 0; gap: 12px; font-size: 13.5px;
}
.ll-md-spec-row .k { color: #6b7686; font-weight: 500; }
.ll-md-spec-row .v { color: var(--ll-ink); font-weight: 650; text-align: right;
  font-feature-settings: 'tnum'; }

/* Description block — softer caption-style block, not a stark blue tag */
.ll-md-desc {
  margin: 22px 0 4px; padding: 14px 18px;
  background: #f7f9fc; border: 1px solid #eef2f7;
  border-radius: 12px; color: #5a6577;
  font-size: 13.5px; line-height: 1.55;
}

/* Request-this-deal: single unified card from header through Send button.
   The form below it gets pulled up and visually merged via negative margin +
   matching white background, so the whole thing reads as one panel. */
.ll-md-req-head {
  display: flex; align-items: center; gap: 14px;
  margin: 28px 0 -6px; padding: 18px 20px 22px;
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fc 100%);
  border: 1px solid #e4ebf3; border-bottom: none;
  border-radius: 14px 14px 0 0;
  box-shadow: 0 1px 2px rgba(14, 42, 71, 0.04);
}
.ll-md-req-ic {
  width: 40px; height: 40px; border-radius: 12px;
  background: #eef4ff; border: 1px solid #d8e6fb;
  display: flex; align-items: center; justify-content: center;
  flex: 0 0 auto;
}
.ll-md-req-head h3 {
  margin: 0; font-size: 16px; font-weight: 750; color: var(--ll-ink);
  letter-spacing: -0.1px;
}
.ll-md-req-head p {
  margin: 2px 0 0; font-size: 13px; color: #6b7686;
}
/* Form container picks up where the header card ends — same border, no top
   edge, completing the unified panel. */
[role="dialog"] [class*="st-key-md_req_wrap_"] {
  padding: 20px 20px 16px !important;
  background: #ffffff !important;
  border: 1px solid #e4ebf3 !important; border-top: none !important;
  border-radius: 0 0 14px 14px !important;
  box-shadow: 0 8px 24px -16px rgba(14, 42, 71, 0.10);
}

/* Tighter form spacing inside the dialog */
[role="dialog"] [data-testid="stForm"] [data-testid="stTextInput"],
[role="dialog"] [data-testid="stForm"] [data-testid="stTextArea"] {
  margin-bottom: 6px !important;
}

@media (max-width: 720px) {
  .ll-md-specs { grid-template-columns: 1fr; }
  .ll-md-price-amt { font-size: 30px; }
  .ll-md-title { font-size: 22px; }
}

/* Admin metric cards */
.ll-mcards { display:flex; gap:16px; flex-wrap:wrap; margin: 2px 0 20px; }
.ll-mcard { flex:1; min-width:175px; display:flex; align-items:center; gap:14px;
  background:#fff; border:1px solid var(--ll-border); border-radius:16px; padding:16px 18px;
  box-shadow:0 1px 2px rgba(16,24,40,.04); }
.ll-mcard-ic { width:46px; height:46px; border-radius:13px; display:flex; align-items:center;
  justify-content:center; flex-shrink:0; }
.ll-mcard-v { font-size:27px; font-weight:820; color:var(--ll-ink); line-height:1.05; letter-spacing:-0.5px; }
.ll-mcard-l { font-size:11.5px; color:var(--ll-muted); text-transform:uppercase; letter-spacing:.5px; margin-top:3px; }

/* Status badge */
.ll-badge { display:inline-block; padding:4px 12px; border-radius:999px; font-size:12.5px; font-weight:750; }

/* Admin section header */
.ll-asec { display:flex; align-items:center; gap:9px; font-size:18px; font-weight:780;
  color:var(--ll-ink); margin: 4px 0 10px; }
.ll-asec svg { width:20px; height:20px; }

/* Info pages (How it works / About) */
.ll-stepnum { width:30px; height:30px; border-radius:50%; background:var(--ll-primary);
  color:#fff; display:flex; align-items:center; justify-content:center; font-weight:800;
  font-size:14px; margin-bottom:2px; }
.ll-cta { display:inline-block; background:var(--ll-primary); color:#fff !important;
  text-decoration:none; font-weight:700; font-size:14.5px; padding:12px 24px; border-radius:10px;
  margin-top:8px; box-shadow:0 8px 20px -10px rgba(99,102,241,0.85); transition:background .15s; }
.ll-cta:hover { background:#1e6fd0; }

footer {visibility:hidden;}

/* ---- Listings page (Carvana-style: light bg, filter rail, results bar) ---- */
[data-testid="stApp"], [data-testid="stAppViewContainer"] { background: #f6f8fb !important; }

/* Give input widgets a visible default border (Streamlit's default bg blends
   into our light page bg, so they look borderless until focused). */
[data-baseweb="select"] > div,
[data-baseweb="input"],
[data-baseweb="textarea"],
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stDateInput"] input {
  background-color: #ffffff !important;
  border: 1px solid #d6dbe5 !important;
  transition: border-color .15s, box-shadow .15s;
}
[data-baseweb="select"] > div:hover,
[data-baseweb="input"]:hover,
[data-testid="stTextInput"] input:hover,
[data-testid="stNumberInput"] input:hover {
  border-color: #b0bac9 !important;
}
[data-baseweb="select"] > div:focus-within,
[data-baseweb="input"]:focus-within,
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
  border-color: var(--ll-primary) !important;
  box-shadow: 0 0 0 1px var(--ll-primary) !important;
}
/* Selectboxes (and multiselects) look like text fields but they're
   click-to-open — show the pointer cursor instead of the text I-beam. */
[data-baseweb="select"] > div,
[data-baseweb="select"] > div * { cursor: pointer !important; }
/* Hide the blinking caret inside the selectbox value display (its hidden
   input is used for type-ahead but shouldn't show a flashing cursor). */
[data-baseweb="select"] input { caret-color: transparent !important; }

.ll-page-intro { padding: 4px 0 8px; }
.ll-page-intro h1 { font-size: 30px; font-weight: 820; color: var(--ll-ink);
  margin: 0 0 4px; letter-spacing:-0.6px; }
.ll-page-intro p { color: var(--ll-muted); font-size: 14.5px; margin: 0; }

/* Filter rail */
.ll-rail-head { display:flex; align-items:center; justify-content:space-between;
  margin: 6px 0 6px; }
.ll-rail-head h3 { font-size:18px; font-weight:820; color:var(--ll-ink); margin:0; letter-spacing:-0.3px; }
.ll-rail-head a { color: var(--ll-primary) !important; font-size:13px; font-weight:650;
  text-decoration:none !important; cursor:pointer; }
/* Flat expander sections (Carvana-style hairlines). Applied globally —
   admin expanders also pick this up, which still looks clean. */
[data-testid="stExpander"] {
  border: none !important; border-radius: 0 !important; background: transparent !important;
  box-shadow: none !important; margin: 0 !important;
}
/* Streamlit wraps the inner UI in <details> with a 1px border + radius and
   gives <summary> a light gray bg — kill both for a flat sectioned look. */
[data-testid="stExpander"] details {
  border: none !important; border-radius: 0 !important;
  background: transparent !important; box-shadow: none !important;
  border-bottom: 1px solid var(--ll-border) !important;
}
[data-testid="stExpander"] summary {
  background: transparent !important;
  padding: 14px 2px !important; cursor: pointer;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
  font-weight: 700 !important; font-size: 14.5px !important; color: var(--ll-ink) !important;
}
[data-testid="stExpander"] summary:hover p,
[data-testid="stExpander"] summary:hover span { color: var(--ll-primary) !important; }

/* Tighter spacing inside filter sections */
.st-key-filterrail [data-testid="stMultiSelect"],
.st-key-filterrail [data-testid="stSlider"],
.st-key-filterrail [data-testid="stTextInput"],
.st-key-filterrail [data-testid="stToggle"],
.st-key-filterrail [data-testid="stCheckbox"] { margin-bottom: 0 !important; }
.st-key-filterrail [data-testid="stExpander"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
/* Long checkbox lists (Make / Model) scroll inside their section, like Carvana. */
.st-key-filterrail [data-testid="stExpander"] details > div { max-height: 320px; overflow-y: auto; padding-top: 4px; padding-bottom: 6px; }
/* Body-type filter: show every option (no internal scroll). */
.st-key-bodytype_filter [data-testid="stExpander"] details > div {
  max-height: none !important; overflow-y: visible !important;
}

/* ===== Filter-rail option rows: hover bg, custom checkbox, tighter rows ===== */
/* Each option row gets a soft hover background and a click target the whole
   width — feels like an iOS/Carvana settings list rather than bare checkboxes. */
.st-key-filterrail [data-testid="stCheckbox"] {
  padding: 6px 6px !important;
  border-radius: 8px !important;
  transition: background-color .12s ease;
}
.st-key-filterrail [data-testid="stCheckbox"]:hover {
  background-color: rgba(46,139,255,0.07) !important;
}
.st-key-filterrail [data-testid="stCheckbox"] label {
  width: 100% !important; cursor: pointer !important;
  align-items: center !important;
}
.st-key-filterrail [data-testid="stCheckbox"] label > div:last-child {
  font-size: 14px !important; font-weight: 500 !important;
  color: var(--ll-ink) !important; line-height: 1.3 !important;
}

/* Custom-styled checkbox square — soft border at rest, branded blue when
   checked. Uses :has(input:checked) so the visual reflects the underlying
   <input> state (BaseWeb doesn't expose aria-checked on the visible span). */
.st-key-filterrail [data-testid="stCheckbox"] label > span:first-child {
  background: #ffffff !important;
  border: 1.5px solid #cdd5e0 !important;
  border-radius: 5px !important;
  width: 18px !important; height: 18px !important;
  transition: border-color .12s, background-color .12s;
}
.st-key-filterrail [data-testid="stCheckbox"]:hover label > span:first-child {
  border-color: var(--ll-primary) !important;
}
.st-key-filterrail [data-testid="stCheckbox"] label:has(input:checked) > span:first-child {
  background-color: var(--ll-primary) !important;
  border-color: var(--ll-primary) !important;
  /* White checkmark drawn as inline SVG so it's guaranteed visible
     regardless of what BaseWeb does (or doesn't) render inside the span. */
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'><path d='M5 12 l5 5 L19 7'/></svg>") !important;
  background-repeat: no-repeat !important;
  background-position: center !important;
  background-size: 12px 12px !important;
}
/* Hide whatever BaseWeb's own check icon is (an inner span / svg) so we don't
   double-up with our drawn checkmark. */
.st-key-filterrail [data-testid="stCheckbox"] label:has(input:checked) > span:first-child > * {
  visibility: hidden !important;
}

/* Compact option rows wrapped in our two-column helper — pull them inward so
   the icon column sits flush with the label column. Force the two columns to
   stay side-by-side at every viewport size (Streamlit otherwise stacks them
   vertically below a width threshold, which throws the icons out of
   alignment with their labels on mobile). */
.st-key-filterrail [data-testid="stHorizontalBlock"] {
  gap: 4px !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
}
.st-key-filterrail [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
  padding: 0 !important;
  width: auto !important;
  flex: 1 1 0 !important;
  min-width: 0 !important;
}

/* Polish expander section headers — accent dot, smooth chevron rotation,
   slightly larger leading. */
.st-key-filterrail [data-testid="stExpander"] details {
  border-bottom: 1px solid var(--ll-border) !important;
}
.st-key-filterrail [data-testid="stExpander"] summary {
  padding: 16px 4px !important;
}
.st-key-filterrail [data-testid="stExpander"] summary p,
.st-key-filterrail [data-testid="stExpander"] summary span {
  font-size: 14px !important; font-weight: 700 !important;
  letter-spacing: 0.1px !important; text-transform: none !important;
}
.st-key-filterrail [data-testid="stExpander"] summary svg {
  transition: transform .2s ease !important;
}
.st-key-filterrail [data-testid="stExpander"] details[open] summary svg {
  color: var(--ll-primary) !important;
}

/* Cap the filter-rail column at 275px wide, let the results column take the
   rest, and make the rail sticky so it follows the user down the listings. */
[data-testid="stHorizontalBlock"]:has(.st-key-filterrail) > [data-testid="stColumn"]:first-child {
  flex: 0 0 275px !important; max-width: 275px !important;
  position: sticky !important;
  top: 84px !important;                       /* just below the fixed nav */
  align-self: flex-start !important;          /* prevent flex stretch */
  max-height: calc(100vh - 100px);            /* scroll internally if tall */
  overflow-y: auto;
  padding-right: 4px;                         /* room for the scrollbar */
}
/* On mobile, the rail becomes a full-screen flyout opened by the "Filter &
   sort" button. Hide the rail column by default, show the toggle button,
   and only display the rail when the marker element is present. */
.st-key-mobile_filter_bar { display: none; }
.st-key-mobile_filter_close { display: none; }
.st-key-mobile_filter_apply { display: none; }
.ll-mobile-filters-marker { display: none !important; height: 0; }

@media (max-width: 880px) {
  /* Show the toggle button at the top of the deals page. */
  .st-key-mobile_filter_bar { display: block !important; margin-bottom: 14px; }
  .st-key-mobile_filter_bar [data-testid="stButton"] > button {
    height: 44px; font-weight: 700; border-radius: 12px;
  }

  /* Hide the filter column by default on mobile (no inline sidebar). */
  [data-testid="stHorizontalBlock"]:has(.st-key-filterrail) > [data-testid="stColumn"]:first-child {
    display: none !important;
  }
  /* Let the results column take the full width. */
  [data-testid="stHorizontalBlock"]:has(.st-key-filterrail) > [data-testid="stColumn"]:last-child {
    flex: 1 1 100% !important; max-width: 100% !important;
  }

  /* === Flyout overlay (when the marker is rendered) === */
  body:has(.ll-mobile-filters-marker) { overflow: hidden !important; }
  body:has(.ll-mobile-filters-marker)
    [data-testid="stHorizontalBlock"]:has(.st-key-filterrail)
    > [data-testid="stColumn"]:first-child {
    display: block !important;
    position: fixed !important;
    top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important;
    height: 100vh !important;
    height: 100dvh !important;              /* dynamic vh for iOS browser chrome */
    width: 100vw !important; max-width: 100vw !important;
    background: #fff !important;
    z-index: 1000010 !important;            /* above the fixed nav */
    overflow-y: auto !important;
    padding: 20px 18px 28px !important;
    max-height: none !important;
    margin: 0 !important;
    box-shadow: 0 0 40px rgba(0,0,0,0.18);
  }
  /* Round ✕ close button pinned to the top-right of the flyout. */
  body:has(.ll-mobile-filters-marker) .st-key-mobile_filter_close {
    display: block !important;
    position: fixed !important;             /* anchor to viewport, not the rail */
    top: 14px !important; right: 14px !important;
    z-index: 1000020 !important;            /* above the rail itself */
    width: auto !important;
  }
  body:has(.ll-mobile-filters-marker) .st-key-mobile_filter_close
    [data-testid="stButton"] > button {
    width: 40px !important; height: 40px !important;
    min-width: 0 !important; padding: 0 !important;
    border-radius: 50% !important;
    background: #ffffff !important;
    border: 1px solid var(--ll-border) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.12) !important;
    color: var(--ll-ink) !important;
    display: flex !important; align-items: center !important; justify-content: center !important;
  }
  body:has(.ll-mobile-filters-marker) .st-key-mobile_filter_close
    [data-testid="stButton"] > button:hover {
    border-color: var(--ll-primary) !important;
    color: var(--ll-primary) !important;
  }
  /* Hide the button's text label so only the ✕ icon shows. (The label is
     needed at the Python level so Streamlit treats it as a stable, named
     widget — empty labels register inconsistently.) */
  body:has(.ll-mobile-filters-marker) .st-key-mobile_filter_close
    [data-testid="stButton"] > button > div:not(:has(svg)),
  body:has(.ll-mobile-filters-marker) .st-key-mobile_filter_close
    [data-testid="stButton"] > button p {
    display: none !important;
  }
  /* Push the rail's "Filters" header down a touch so it doesn't sit under
     the floating close button. */
  body:has(.ll-mobile-filters-marker) .st-key-filterrail > div:first-child {
    margin-top: 4px;
  }

  /* Sticky "Apply filters · N results" button pinned to the bottom of the
     flyout. Anchored to the viewport (not the rail) so it stays visible
     while the filters scroll behind it. */
  body:has(.ll-mobile-filters-marker) .st-key-mobile_filter_apply {
    display: block !important;
    position: fixed !important;
    left: 14px !important; right: 14px !important;
    bottom: 14px !important;
    z-index: 1000020 !important;
    width: auto !important;
  }
  body:has(.ll-mobile-filters-marker) .st-key-mobile_filter_apply
    [data-testid="stButton"] > button {
    height: 52px !important;
    font-size: 15px !important; font-weight: 700 !important;
    border-radius: 14px !important;
    box-shadow: 0 8px 24px rgba(46,139,255,0.32) !important;
  }
  /* Add room at the bottom of the flyout content so the last filter isn't
     hidden under the floating Apply button. */
  body:has(.ll-mobile-filters-marker)
    [data-testid="stHorizontalBlock"]:has(.st-key-filterrail)
    > [data-testid="stColumn"]:first-child {
    padding-bottom: 100px !important;
  }
}

/* Filters rail header */
.ll-rail-heading { display:flex; align-items:center; justify-content:space-between;
  gap:8px; padding:2px 2px 6px; }
.ll-rail-heading h3 { font-size:18px; font-weight:820; color:var(--ll-ink);
  margin:0; letter-spacing:-0.3px; display:flex; align-items:center; gap:8px; }
.ll-rail-heading svg { width:18px; height:18px; }

/* Selection count badge for section titles */
.ll-sec-count {
  display:inline-block; background:var(--ll-primary); color:#fff;
  font-size:11px; font-weight:700; padding:1px 8px; border-radius:999px;
  margin-left:6px; vertical-align:middle;
}

/* Results bar */
.ll-results-count { font-size:24px; font-weight:820; color:var(--ll-ink);
  letter-spacing:-0.5px; margin: 4px 0 6px; }
.ll-results-count small { font-size:14px; font-weight:600; color:var(--ll-muted); margin-left:8px; }
.ll-active-chips { display:flex; gap:6px; flex-wrap:wrap; margin: 6px 0 16px; }
.ll-filter-chip {
  background:#eef2f8; color:var(--ll-ink); padding:5px 12px; border-radius:999px;
  font-size:12.5px; font-weight:650;
}

/* Active filter chips rendered as Streamlit buttons (click × to remove the
   matching filter). Force the column-stacked buttons into a flowing row. */
.st-key-active_chips,
.st-key-active_chips > div,
.st-key-active_chips [data-testid="stVerticalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: wrap !important;
  gap: 6px !important;
  align-items: center !important;
}
.st-key-active_chips { margin: 6px 0 14px !important; }
.st-key-active_chips [data-testid="stElementContainer"],
.st-key-active_chips [data-testid="stButton"] {
  width: auto !important;
  min-width: 0 !important;
  flex: 0 0 auto !important;
  margin: 0 !important;
}
.st-key-active_chips [data-testid="stButton"] > button {
  background: #eef2f8 !important;
  color: var(--ll-ink) !important;
  border: 1px solid #d6dbe5 !important;
  padding: 3px 12px !important;
  height: auto !important; min-height: 0 !important;
  width: auto !important;
  border-radius: 999px !important;
  font-size: 12.5px !important; font-weight: 650 !important;
  line-height: 1.7 !important; white-space: nowrap !important;
  transition: background .12s, color .12s, border-color .12s;
}
.st-key-active_chips [data-testid="stButton"] > button:hover {
  background: var(--ll-primary) !important;
  color: #ffffff !important;
  border-color: var(--ll-primary) !important;
}
.ll-results-divider { border-top:1px solid var(--ll-border); margin: 4px 0 18px; }

/* ============================================================ Homepage */
.ll-home-hero {
  position: relative; overflow: hidden;
  margin: 8px 0 32px; padding: 72px 36px 64px;
  background:
    radial-gradient(60% 80% at 85% 10%, rgba(46,139,255,0.22) 0%, transparent 60%),
    radial-gradient(50% 80% at 10% 90%, rgba(46,139,255,0.15) 0%, transparent 60%),
    linear-gradient(135deg, #112949 0%, #0E2A47 50%, #081a30 100%);
  color: #fff; border-radius: 22px; text-align: center;
  box-shadow: 0 24px 60px -24px rgba(14,42,71,0.45);
}
.ll-home-hero::before {
  /* faint dotted texture so the panel doesn't read as flat color */
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background-image: radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px);
  background-size: 18px 18px; opacity: .6;
}
.ll-home-hero > * { position: relative; }

.ll-hero-eyebrow {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; margin: 0 0 18px;
  background: rgba(46,139,255,0.14); color: #9bc0ff;
  border: 1px solid rgba(122,169,255,0.28);
  border-radius: 999px; font-size: 12px; font-weight: 650;
  letter-spacing: 0.4px; text-transform: uppercase;
}
.ll-home-hero h1 {
  margin: 0 0 14px; font-size: 44px; line-height: 1.1;
  font-weight: 800; letter-spacing: -0.8px;
}
.ll-home-hero p {
  margin: 0 auto 28px; max-width: 680px; color: #c9d3e3;
  font-size: 17px; line-height: 1.55;
}

.ll-hero-ctas {
  display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;
  margin-bottom: 26px;
}
.ll-hero-cta {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 12px 22px; border-radius: 999px;
  font-size: 15px; font-weight: 650; text-decoration: none !important;
  transition: transform .12s, background .12s, border-color .12s, box-shadow .12s;
  cursor: pointer; user-select: none;
}
.ll-hero-cta.primary {
  background: var(--ll-primary); color: #fff !important;
  box-shadow: 0 8px 20px -6px rgba(46,139,255,0.55);
}
.ll-hero-cta.primary:hover { transform: translateY(-1px); background: #1d7aee; }
.ll-hero-cta.ghost {
  background: transparent; color: #e8eef9 !important;
  border: 1px solid rgba(255,255,255,0.22);
}
.ll-hero-cta.ghost:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.4); }

.ll-hero-trust {
  display: flex; justify-content: center; gap: 22px; flex-wrap: wrap;
  color: #8ea3c1; font-size: 13px; font-weight: 500;
  padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.08);
  margin-top: 8px; padding: 18px 0 0;
}
.ll-hero-trust span { display: inline-flex; align-items: center; gap: 6px; }

.ll-home-h {
  font-size: 26px; font-weight: 750; margin: 40px 0 18px; color: var(--ll-ink);
  letter-spacing: -0.3px; text-align: center;
}

.ll-tiles {
  display: flex; flex-wrap: wrap; gap: 14px;
  justify-content: center;
  max-width: 1080px; margin: 0 auto 28px;
}
.ll-tile { flex: 0 0 160px; }

/* Top deals row — cap width and center within the page. */
.st-key-home_top_deals {
  max-width: 1080px; margin: 0 auto 14px;
}
.ll-tile {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-decoration: none !important; color: var(--ll-ink) !important;
  padding: 18px 12px; background: #fff;
  border: 1px solid var(--ll-border); border-radius: 14px;
  transition: transform .12s, border-color .12s, box-shadow .12s;
  min-height: 130px;
  cursor: pointer; user-select: none;
}
.ll-tile:hover {
  transform: translateY(-2px);
  border-color: var(--ll-primary);
  box-shadow: 0 8px 20px rgba(46,139,255,0.15);
}
.ll-tile-ic { height: 72px; display: flex; align-items: center; justify-content: center;
  margin-bottom: 10px; }
.ll-tile-ic > div { margin: 0 auto !important; justify-content: center !important; }
.ll-tile-ic img { max-height: 72px; width: auto; object-fit: contain; }
.ll-tile-lab { font-size: 15px; font-weight: 650; color: var(--ll-ink); }
.ll-tile-ct  { font-size: 12px; color: #6b7686; margin-top: 2px; }

/* Sign-and-Drive premium-upsell band — homepage, between Top Deals and
   Shop by Make. Dark navy gradient pulls the eye after the inventory grid
   without competing with the lighter sections around it. */
.ll-snd-band {
  position: relative; overflow: hidden;
  margin: 40px 0 28px; padding: 36px 40px;
  background:
    radial-gradient(60% 100% at 90% 10%, rgba(46,139,255,0.22) 0%, transparent 60%),
    linear-gradient(135deg, #0E2A47 0%, #112949 100%);
  border-radius: 20px; color: #fff;
  display: grid; grid-template-columns: 1fr auto;
  align-items: center; gap: 32px;
  box-shadow: 0 20px 60px -30px rgba(14, 42, 71, 0.50);
}
.ll-snd-band::before {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background-image: radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px);
  background-size: 18px 18px;
}
.ll-snd-band > * { position: relative; }
.ll-snd-eyebrow {
  display: inline-flex; align-items: center; gap: 6px;
  font-size: 11.5px; font-weight: 750; letter-spacing: 0.6px;
  text-transform: uppercase; color: #7aa9ff;
  margin-bottom: 14px;
}
.ll-snd-band h2 {
  margin: 0 0 12px; font-size: 28px; font-weight: 820;
  letter-spacing: -0.6px; line-height: 1.15; color: #fff;
}
.ll-snd-band p {
  margin: 0; font-size: 15px; line-height: 1.55;
  color: #cdd6e4; max-width: 580px;
}
.ll-snd-feats {
  display: flex; flex-wrap: wrap; gap: 20px 24px;
  margin: 18px 0 0; font-size: 13px; color: #b3c0d4; font-weight: 600;
}
.ll-snd-feat { display: inline-flex; align-items: center; gap: 6px; }
.ll-snd-cta {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 24px; border-radius: 999px;
  background: #2E8BFF; color: #fff !important; text-decoration: none;
  font-weight: 700; font-size: 14px; white-space: nowrap;
  box-shadow: 0 8px 24px -8px rgba(46, 139, 255, 0.65);
  transition: transform .15s ease, box-shadow .15s ease;
}
.ll-snd-cta:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 32px -8px rgba(46, 139, 255, 0.75);
}
@media (max-width: 720px) {
  .ll-snd-band { grid-template-columns: 1fr; padding: 28px 24px; }
  .ll-snd-band h2 { font-size: 22px; }
}

/* "How it works" panel — same dark gradient + dotted texture treatment as
   the home hero, with glass-card steps on top. */
.ll-hiw-panel {
  position: relative; overflow: hidden;
  margin: 36px 0 24px; padding: 56px 36px 52px;
  background:
    radial-gradient(60% 80% at 85% 10%, rgba(46,139,255,0.22) 0%, transparent 60%),
    radial-gradient(50% 80% at 10% 90%, rgba(46,139,255,0.15) 0%, transparent 60%),
    linear-gradient(135deg, #112949 0%, #0E2A47 50%, #081a30 100%);
  color: #fff; border-radius: 22px; text-align: center;
  box-shadow: 0 24px 60px -24px rgba(14,42,71,0.45);
}
.ll-hiw-panel::before {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background-image: radial-gradient(rgba(255,255,255,0.06) 1px, transparent 1px);
  background-size: 18px 18px; opacity: .6;
}
.ll-hiw-panel > * { position: relative; }
.ll-hiw-eyebrow {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; margin: 0 0 16px;
  background: rgba(46,139,255,0.14); color: #9bc0ff;
  border: 1px solid rgba(122,169,255,0.28);
  border-radius: 999px; font-size: 12px; font-weight: 650;
  letter-spacing: 0.4px; text-transform: uppercase;
}
.ll-hiw-panel h2 {
  margin: 0 0 10px; font-size: 32px; line-height: 1.15;
  font-weight: 800; letter-spacing: -0.6px; color: #fff;
}
.ll-hiw-panel p {
  margin: 0 auto 32px; max-width: 600px; color: #c9d3e3;
  font-size: 16px; line-height: 1.55;
}

.ll-hiw {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
  text-align: left;
}
.ll-hiw-step {
  position: relative;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 16px; padding: 26px 22px 24px;
  backdrop-filter: blur(6px);
  transition: transform .15s ease, border-color .15s ease, background .15s ease;
}
.ll-hiw-step:hover {
  transform: translateY(-2px);
  border-color: rgba(122,169,255,0.40);
  background: rgba(255,255,255,0.06);
}
.ll-hiw-num {
  position: absolute; top: 18px; right: 20px;
  font-size: 13px; font-weight: 800; letter-spacing: 1px;
  color: rgba(155,192,255,0.55); font-feature-settings: 'tnum';
}
.ll-hiw-ic {
  width: 44px; height: 44px; border-radius: 12px;
  background: rgba(46,139,255,0.18);
  border: 1px solid rgba(122,169,255,0.28);
  color: #7aa9ff;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.ll-hiw-t {
  font-size: 17px; font-weight: 700; color: #ffffff;
  margin-bottom: 8px; letter-spacing: -0.1px;
}
.ll-hiw-d {
  font-size: 14px; color: #b3c0d4; line-height: 1.55;
}

/* About — live-stats strip just under the hero. Light cards, big numbers. */
.ll-about-stats {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
  max-width: 880px; margin: 0 auto 36px;
}
.ll-about-stat {
  background: #fff; border: 1px solid var(--ll-border);
  border-radius: 14px; padding: 20px 16px; text-align: center;
  box-shadow: 0 4px 14px -8px rgba(14,42,71,0.10);
}
.ll-about-stat-n {
  font-size: 30px; font-weight: 800; color: var(--ll-ink);
  letter-spacing: -0.6px; font-feature-settings: 'tnum';
  line-height: 1.1; margin-bottom: 4px;
}
.ll-about-stat-l {
  font-size: 12.5px; font-weight: 650; color: #6b7686;
  text-transform: uppercase; letter-spacing: 0.4px;
}
@media (max-width: 720px) {
  .ll-about-stats { grid-template-columns: repeat(2, 1fr); }
  .ll-about-stat-n { font-size: 24px; }
}

/* "Why the numbers matter" — clean white card between the two dark panels
   so the page has visual breathing room. */
.ll-why {
  margin: 28px auto; padding: 36px 32px; max-width: 760px;
  background: #fff; border: 1px solid var(--ll-border);
  border-radius: 18px; text-align: center;
  box-shadow: 0 6px 20px -10px rgba(14,42,71,0.10);
}
.ll-why-ic {
  width: 48px; height: 48px; border-radius: 12px;
  background: rgba(46,139,255,0.10); color: var(--ll-primary);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 14px;
}
.ll-why h2 {
  margin: 0 0 10px; font-size: 24px; font-weight: 750;
  color: var(--ll-ink); letter-spacing: -0.3px;
}
.ll-why p {
  margin: 0 auto; max-width: 580px; font-size: 15px;
  line-height: 1.65; color: #4a5666;
}

/* Bottom CTA strip — light, centered, simple. */
.ll-hiw-cta {
  margin: 28px 0 8px; padding: 36px 24px; text-align: center;
}
.ll-hiw-cta h2 {
  margin: 0 0 6px; font-size: 26px; font-weight: 800;
  color: var(--ll-ink); letter-spacing: -0.3px;
}
.ll-hiw-cta p {
  margin: 0 0 20px; color: #6b7686; font-size: 15px;
}

@media (max-width: 720px) {
  .ll-home-hero { padding: 44px 18px 36px; margin: 4px 0 22px; border-radius: 16px; }
  .ll-home-hero h1 { font-size: 28px; line-height: 1.12; }
  .ll-home-hero p { font-size: 15px; }
  .ll-hero-trust { gap: 10px; font-size: 12px; }
  .ll-hero-cta { padding: 10px 18px; font-size: 14px; }
  .ll-hiw-panel { padding: 36px 18px 32px; border-radius: 16px; }
  .ll-hiw-panel h2 { font-size: 22px; }
  .ll-hiw-panel p { font-size: 14px; }
  .ll-hiw { grid-template-columns: 1fr; gap: 12px; }
  .ll-hiw-step { padding: 20px 18px 18px; }
  .ll-why { padding: 28px 20px; border-radius: 14px; }
  .ll-why h2 { font-size: 20px; }
  .ll-hiw-cta { padding: 28px 16px; }
  .ll-hiw-cta h2 { font-size: 20px; }
  /* Section headings tighter on mobile so they don't feel oversized */
  .ll-home-h { font-size: 22px; margin: 28px 0 14px; }
  /* Tile cells shrink so 2 fit per row on a 350px viewport */
  .ll-tile { flex: 0 0 calc(50% - 7px); min-width: 0; }
  .ll-tile-ic { height: 60px; }
}
@media (max-width: 380px) {
  .ll-home-hero { padding: 36px 14px 30px; }
  .ll-home-hero h1 { font-size: 24px; }
  .ll-hero-trust span { font-size: 11px; }
}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, icon_svg: str = ""):
    icon_html = f"<span class='ll-hero-ic'>{icon_svg}</span>" if icon_svg else ""
    st.markdown(
        f"<div class='ll-hero'><div class='ll-hero-top'>{icon_html}<h1>{title}</h1></div>"
        f"<p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def top_nav(active_path: str = ""):
    """Render the branded, customer-facing top navigation. No admin links here —
    the admin area is reachable only via URL (/admin) and shows its own sub-nav."""
    from .icons import logo

    public = [("", "Home"),
              ("deals", "Browse Deals"),
              ("how-it-works", "How It Works"),
              ("dealers", "For Dealers"),
              ("about", "About")]

    # Plain anchors. Streamlit strips inline onclick handlers from
    # unsafe_allow_html, so JS-based navigation doesn't work. ``target='_self'``
    # keeps clicks in the same tab; URL-bar update on .streamlit.app
    # subdomains is limited by the Streamlit Cloud iframe wrapper (will work
    # on a custom domain).
    items = ""
    for path, label in public:
        cls = "ll-navlink active" if path == active_path else "ll-navlink"
        href = "/" if path == "" else f"/{path}"
        items += f"<a class='{cls}' href='{href}' target='_self'>{label}</a>"

    # Official primary horizontal logo (navy + blue, sits on the white header).
    brand = brand_svg("acd-primary-horizontal.svg") or (logo(36) + "<span>ALL CARS DIRECT</span>")

    html = (
        f"<div class='ll-nav-wrap'><div class='ll-nav'>"
        f"<a class='ll-brand-link' href='/' target='_self'>{brand}</a>"
        f"<div class='ll-nav-right'>"
        f"<nav class='ll-navlinks'>{items}</nav>"
        f"<a class='ll-nav-cta' href='mailto:info@allcarsdirectllc.com'>Contact us</a>"
        f"</div>"
        f"</div></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def metric_cards(cards):
    """Render a row of admin metric cards. cards: list of (icon_name, value, label, hex_color)."""
    from .icons import icon

    html = "<div class='ll-mcards'>"
    for ic, value, label, color in cards:
        html += (
            f"<div class='ll-mcard'>"
            f"<div class='ll-mcard-ic' style='background:{color}1f'>{icon(ic, 22, color)}</div>"
            f"<div><div class='ll-mcard-v'>{value}</div><div class='ll-mcard-l'>{label}</div></div>"
            f"</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


_STATUS_COLORS = {"New": "#f59e0b", "Contacted": "#0ea5e9", "Closed": "#16a34a"}


def status_badge(status: str) -> str:
    """Return an HTML pill for an inquiry status (use inside st.markdown)."""
    color = _STATUS_COLORS.get(status, "#6b7280")
    return f"<span class='ll-badge' style='background:{color}1f;color:{color}'>{status}</span>"


def asection(label: str, icon_name: str = "", color: str = "#2E8BFF"):
    """Render a styled admin section header with an optional inline icon."""
    from .icons import icon as _icon

    ic = _icon(icon_name, 20, color) if icon_name else ""
    st.markdown(f"<div class='ll-asec'>{ic}<span>{label}</span></div>", unsafe_allow_html=True)


def admin_subnav(active_path: str = ""):
    """Secondary nav shown only on admin pages (back-office navigation)."""
    from .auth import DISABLE_AUTH

    admin = [("admin", "Dashboard"), ("admin-requests", "Requests"),
             ("admin-listings", "Manage"), ("admin-upload", "Upload"),
             ("admin-sources", "Sources")]

    items = ""
    for path, label in admin:
        cls = "ll-subnavlink active" if path == active_path else "ll-subnavlink"
        items += f"<a class='{cls}' href='/{path}' target='_self'>{label}</a>"
    if not DISABLE_AUTH:
        items += "<a class='ll-subnavlink ll-logout' href='/?logout=1' target='_self'>Log out</a>"

    html = (
        f"<div class='ll-subnav'><span class='ll-subnav-label'>ADMIN</span>"
        f"<nav>{items}</nav></div>"
    )
    st.markdown(html, unsafe_allow_html=True)
