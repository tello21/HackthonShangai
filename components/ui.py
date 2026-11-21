"""Small UI helpers shared by the pages: formatting, tags, images, links, navigation,
the product card and the delivered-price receipt."""

import base64
import html
from urllib.parse import quote

import streamlit as st

from components.state import S, link
from core import profile as P
from core.catalog import CATEGORY_STYLE
from core.pricing import CURRENCY_NAMES, SYMBOL, fx_info, fx_rate

NA = "not available"
PLATFORM_COLOURS = {"1688": "#FF6A00", "Taobao": "#F5A623", "JD": "#7B3FE4", "Pinduoduo": "#E02E24"}


# ---------------------------------------------------------------------------- formatting
def money(v, sym, decimals=2):
    return NA if v is None else f"{sym}{v:,.{decimals}f}"


def units(n):
    return f"{n:,} unit" + ("" if n == 1 else "s")


def cny(v):
    return NA if v is None else f"¥{v:,.2f}"


def esc(s):
    return html.escape(str(s)) if s is not None else ""


def tag(text, kind="sample"):
    return f"<span class='tag tag-{kind}'>{text}</span>"


def currency_label(c):
    sym = SYMBOL[c].strip()
    return f"{sym} {CURRENCY_NAMES[c]}" if sym != c else f"{c} · {CURRENCY_NAMES[c]}"


def currency_short(c):
    sym = SYMBOL[c].strip()
    return f"{sym} {c}" if sym != c else c


def fx_line(currency):
    """Where the exchange rate comes from, shown next to converted prices."""
    if currency == "CNY":
        return "Prices in Chinese yuan, no conversion"
    info = fx_info()
    rate = f"1 CNY = {SYMBOL[currency]}{fx_rate(currency):,.4f}"
    if info["live"]:
        return f"{rate} · ECB reference rate of {info['date']}"
    return f"{rate} · sample rate (live ECB rate unavailable)"


def fx_line_short():
    if S.cur == "CNY":
        return "prices in CNY"
    info = fx_info()
    return f"ECB rate {info['date']}" if info["live"] else "sample exchange rate"


DARK_TEXT_BANDS = {"Good", "Caution"}   # light green / yellow need dark text


def trust_pill(r, big=False):
    """Coloured trust band: 'Trust 84 · Trusted', or 'Trust n/a · Not enough data'."""
    fg = "#0B2A47" if r["band"] in DARK_TEXT_BANDS else "#fff"
    txt = f"Trust {r['score']} · {r['band']}" if r["score"] is not None else f"Trust n/a · {r['band']}"
    cls = "score-pill big" if big else "sc"
    return f"<span class='{cls}' style='background:{r['colour']};color:{fg}'>{esc(txt)}</span>"


def demo_tag(p):
    """Small label for listings with some made-up values (notes_en starts with 'DEMO:')."""
    return "<span class='demo-tag'>demo data</span>" if p.get("demo") else ""


def trust_bars(r):
    """One horizontal bar per metric with its weight and reason; missing ones in grey."""
    rows = []
    for m in r["metrics"]:
        if m["value"] is None:
            rows.append(f"<div class='tm na'><div class='tm-top'><span>{esc(m['name'])} <small>· {m['weight']}%</small>"
                        f"</span><span>not available</span></div><div class='tm-bar'></div>"
                        f"<div class='tm-why'>{esc(m['reason'])}</div></div>")
        else:
            rows.append(f"<div class='tm'><div class='tm-top'><span>{esc(m['name'])} <small>· {m['weight']}%</small>"
                        f"</span><b>{m['value']}</b></div><div class='tm-bar'><div class='tm-fill' "
                        f"style='width:{m['value']}%'></div></div><div class='tm-why'>{esc(m['reason'])}</div></div>")
    return "<div class='tms'>" + "".join(rows) + "</div>"


def platform_tag(platform):
    return (f"<span class='mk' style='background:{PLATFORM_COLOURS.get(platform, '#6b7280')}'>"
            f"{esc(platform or NA)}</span>")


def section(n, title):
    """Numbered section heading of the product sheet."""
    return f"<div class='sec-h'><span class='sec-n'>{n}</span>{esc(title)}</div>"


def fact_grid(items):
    """Tiles instead of a two-column table: small label on top, value below.
    items: (label, value_html or None, wide). None -> a muted 'not available' tile."""
    tiles = []
    for label, value, *wide in items:
        cls = "fact" + (" wide" if wide and wide[0] else "") + (" na-tile" if value in (None, "") else "")
        shown = value if value not in (None, "") else NA
        tiles.append(f"<div class='{cls}'><div class='fact-l'>{esc(label)}</div><div class='fact-v'>{shown}</div></div>")
    return "<div class='facts'>" + "".join(tiles) + "</div>"


def tier_cards(tiers, qty, currency):
    """The seller's quantity price tiers as cards; the tier for the chosen quantity is marked."""
    tiers = sorted(tiers)
    fx, sym = fx_rate(currency), SYMBOL[currency]
    active = max((i for i, (mq, _) in enumerate(tiers) if qty >= mq), default=None)
    first = tiers[0][1]
    cards = []
    for i, (mq, price) in enumerate(tiers):
        rng = f"{mq:,}–{tiers[i + 1][0] - 1:,}" if i + 1 < len(tiers) else f"{mq:,}+"
        conv = f"≈ {sym}{price * fx:,.2f}" if currency != "CNY" else ""
        off = f"<span class='tier-off'>−{(first - price) / first * 100:.0f}%</span>" if price < first else ""
        mark = "<span class='tier-you'>Your quantity</span>" if i == active else ""
        cards.append(f"<div class='tier{' on' if i == active else ''}'>{mark}"
                     f"<div class='tier-q'>{rng} units</div>"
                     f"<div class='tier-p'>¥{price:,.2f}<small>/unit</small></div>"
                     f"<div class='tier-c'>{conv}{off}</div></div>")
    return "<div class='tiers'>" + "".join(cards) + "</div>"


# ---------------------------------------------------------------------------- images and links
def image_uri(p, square=False):
    """The product photo (catalog: app/static/images/..., or a web link), else a placeholder."""
    picture = p.get("picture")
    if isinstance(picture, str) and picture.startswith(("http", "app/static/")):
        return picture
    emoji, colour = CATEGORY_STYLE.get(p.get("category") or "unknown", CATEGORY_STYLE["unknown"])
    w, h = (220, 220) if square else (300, 220)
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>
<rect width='{w}' height='{h}' rx='14' fill='{colour}'/>
<text x='{w/2}' y='{h/2 + 25}' font-size='86' text-anchor='middle'>{emoji}</text>
<text x='{w/2}' y='{h - 20}' font-size='15' text-anchor='middle' fill='#555' font-family='sans-serif'>No photo</text>
</svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


def platform_search_url(platform, keywords):
    kw = quote(keywords or "")
    return {
        "1688": f"https://s.1688.com/selloffer/offer_search.htm?keywords={kw}",
        "Taobao": f"https://s.taobao.com/search?q={kw}",
        "JD": f"https://search.jd.com/Search?keyword={kw}",
        "Pinduoduo": f"https://mobile.yangkeduo.com/search_result.html?search_key={kw}",
    }.get(platform)


def search_link(p):
    """For listings without a link: a search on the platform instead."""
    return platform_search_url(p.get("platform"), p.get("title_cn") or p.get("title_en"))


# ---------------------------------------------------------------------------- navigation
def unread_count():
    return sum(1 for c in S.convs.values() for m in c["messages"]
               if m["role"] == "supplier" and not m.get("read"))


MARK_SVG = ("<span class='mark'><svg fill='none' stroke='#fff' stroke-linecap='round' stroke-width='2.4' "
            "viewBox='0 0 24 24'><circle cx='10' cy='10' r='6'></circle><path d='m14.8 14.8 5 5'></path></svg></span>")


def brand_html():
    return (f"<a class='brand' href='{link(view='home', tab='search', pid=None)}' target='_self'>"
            f"{MARK_SVG}SourceScan</a>")


def topbar_html():
    """Brand on the left; Search, Link paste, Messages, Profile, FAQ and the delivery chip on the right."""
    def a(label, view, cls="", **kw):
        on = " on" if S.view == view else ""
        return f"<a class='{cls}{on}' href='{link(view=view, **kw)}' target='_self'>{label}</a>"
    n = unread_count()
    links = [a("Search", "home", "hide-sm", tab="search", pid=None),
             a("Link paste", "paste", "hide-sm", pid=None),
             a("Messages" + (f" <span class='unread-badge'>{n}</span>" if n else ""), "inbox", pid=None),
             a(f"<span class='avatar'>{esc(P.initials(S.profile))}</span>Profile", "profile", "avatar-link",
               order=None)]
    if len(S.cmp) >= 2:
        links.append(a(f"Compare ({len(S.cmp)})", "compare"))
    links.append(f"<a class='hide-sm' href='{link(view='home', tab='search', pid=None)}#faq' target='_self'>FAQ</a>")
    links.append(f"<span class='locale'>{esc(S.country)} · {currency_short(S.cur)}</span>")
    return f"<div class='topbar'>{brand_html()}<div class='top-links'>{''.join(links)}</div></div>"


def band(key="band"):
    """The light full-width top bar. Use as `with band(): ...` to add content right below it."""
    c = st.container(key=key)
    c.markdown(topbar_html(), unsafe_allow_html=True)
    return c


def nav_bar():
    """Top bar for inner pages."""
    band()


def pagehero(tag_text, title, sub="", steps=None):
    """Centred page heading of the inner pages; steps = index of the active 01 Search · 02 Compare · 03 Checkout."""
    prog = ""
    if steps is not None:
        names = ["01 Search", "02 Compare", "03 Checkout"]
        prog = "<div class='progress'>" + "—".join(
            f"<span class='{'on' if i == steps else ''}'>{n}</span>" for i, n in enumerate(names)) + "</div>"
    return (f"<div class='pagehero'><div class='sectiontag'>{esc(tag_text)}</div><div class='ph1'>{title}</div>"
            + (f"<div class='psub'>{sub}</div>" if sub else "") + f"</div>{prog}")


def site_footer():
    links = "".join(f"<a href='{u}' target='_self'>{t}</a>" for t, u in [
        ("Search", link(view="home", tab="search", pid=None)), ("Link paste", link(view="paste", pid=None)),
        ("Messages", link(view="inbox", pid=None)), ("Profile", link(view="profile", order=None)),
        ("FAQs", link(view="home", tab="search", pid=None) + "#faq")])
    st.markdown(
        f"<div class='sitefoot'><div>{brand_html()}<p class='disclaimer'>Hackathon prototype. Listings come from a "
        "fixed catalog collected from 1688, Taobao, JD and Pinduoduo, not a live search; payments are simulated. "
        "Trust scores summarize available public signals and are not official verification. Delivered prices "
        "are estimates until final quotes and customs details are confirmed. No affiliation with the "
        f"marketplaces is implied.</p></div><div class='footlinks'>{links}</div></div>", unsafe_allow_html=True)


def sample_banner():
    st.markdown(tag("Delivered prices are estimates", "est"), unsafe_allow_html=True)


def scroll_to_top_on_view_change():
    view = f"{S.view}:{S.pid if S.view == 'detail' else ''}:{S.tab if S.view == 'home' else ''}"
    if S.get("_last_view") != view:
        S._last_view = view
        # run after the new page has rendered (Streamlit keeps the old scroll position otherwise)
        # (own scope: st.html scripts share the page's global scope; the view name makes the HTML
        # differ from page to page, otherwise Streamlit keeps the old element and the script won't rerun)
        # an address ending in #faq (the FAQ link) scrolls to that section instead
        st.html(f"<script data-view='{html.escape(view)}'>(() => {{ const up = () => {{"
                "const t = location.hash ? document.getElementById(location.hash.slice(1)) : null;"
                "if (t) {{ t.scrollIntoView(); return; }}"
                "const m = document.querySelector('[data-testid=\"stMain\"]');"
                "if (m) m.scrollTo(0, 0); window.scrollTo(0, 0); };"
                "setTimeout(up, 80); setTimeout(up, 400); setTimeout(up, 900); })();</script>",
                unsafe_allow_javascript=True)


# ---------------------------------------------------------------------------- receipt
def receipt(lines, total_label, total_note, total, per_unit_total, qty, sym):
    """Delivered-price breakdown as a phone-friendly receipt.
    lines: [(label, amount or None, basis text), ...]"""
    def amount(v):
        if v is None:
            return f"<span class='na'>{NA}</span>"
        return (f"<span class='ra-main'>{money(v, sym)}</span>"
                f"<span class='ra-per'>{money(v / qty, sym, 3)}/unit</span>")

    rows = "".join(f"<div class='rr'><div class='rl'>{esc(n)}<span class='rb'>{esc(b)}</span></div>"
                   f"<div class='ra'>{amount(v)}</div></div>" for n, v, b in lines)
    tot = (f"<span class='na'>{NA}</span>" if total is None else
           f"<span class='ra-main'>{money(total, sym)}</span><span class='ra-per'>{money(per_unit_total, sym, 3)}/unit</span>")
    return (f"<div class='rcpt'>{rows}<div class='rr rt'><div class='rl'>{esc(total_label)}"
            f"<span class='rb'>{esc(total_note)}</span></div><div class='ra'>{tot}</div></div></div>")
