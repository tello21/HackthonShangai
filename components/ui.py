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
PLATFORM_COLOURS = {"1688": "#FF6A00", "Taobao": "#F5A623", "JD": "#7B3FE4", "Yiwugo": "#1E73BE"}


# ---------------------------------------------------------------------------- formatting
def money(v, sym, decimals=2):
    return NA if v is None else f"{sym}{v:,.{decimals}f}"


def units(n):
    return f"{n:,} unit" + ("" if n == 1 else "s")


def cny(v):
    return NA if v is None else f"¥{v:,.2f}"


def val(v, suffix=""):
    if v is None or v == "" or v == []:
        return f"<span class='na'>{NA}</span>"
    return f"{v}{suffix}"


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


def trust_reasons_line(r, n=2):
    """The strongest signals for a result card."""
    return " · ".join(esc(x) for x in r["reasons"][:n])


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


def kv_table(pairs):
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in pairs)
    return f"<table class='kv'>{rows}</table>"


# ---------------------------------------------------------------------------- images and links
def image_uri(p, square=False):
    picture = p.get("picture")
    if isinstance(picture, str) and picture.startswith("http"):
        return picture
    emoji, colour = CATEGORY_STYLE.get(p.get("category") or "unknown", CATEGORY_STYLE["unknown"])
    w, h = (220, 220) if square else (300, 220)
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>
<rect width='{w}' height='{h}' rx='14' fill='{colour}'/>
<text x='{w/2}' y='{h/2 + 25}' font-size='86' text-anchor='middle'>{emoji}</text>
<text x='{w/2}' y='{h - 20}' font-size='15' text-anchor='middle' fill='#555' font-family='sans-serif'>Sample image</text>
</svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


def image_html(p, height=150):
    return (f"<img src='{image_uri(p)}' "
            f"style='width:100%;max-height:{height}px;object-fit:contain;border-radius:12px'/>")


def platform_search_url(platform, keywords):
    kw = quote(keywords or "")
    return {
        "1688": f"https://s.1688.com/selloffer/offer_search.htm?keywords={kw}",
        "Taobao": f"https://s.taobao.com/search?q={kw}",
        "JD": f"https://search.jd.com/Search?keyword={kw}",
        "Yiwugo": f"https://www.yiwugo.com/search?q={kw}",
    }.get(platform)


def search_link(p):
    """Sample products have no real listing; offer a platform search instead."""
    return platform_search_url(p.get("platform"), p.get("title_cn") or p.get("title_en"))


# ---------------------------------------------------------------------------- navigation
def unread_count():
    return sum(1 for c in S.convs.values() for m in c["messages"]
               if m["role"] == "supplier" and not m.get("read"))


def messages_link():
    n = unread_count()
    badge = f" <span class='unread-badge'>{n}</span>" if n else ""
    return (f"<a class='plain msg-link' href='{link(view='inbox', pid=None)}' target='_self'>"
            f"Messages{badge}</a>")


def topbar_html():
    """Logo on the left; sections, orders and the delivery chip on the right."""
    links = [f"<a href='{link(view='home', tab='link', pid=None)}' target='_self'>Link paste</a>",
             messages_link(),
             f"<a class='avatar-link' href='{link(view='profile', order=None)}' target='_self'>"
             f"<span class='avatar'>{esc(P.initials(S.profile))}</span>Profile</a>"]
    if len(S.cmp) >= 2:
        links.append(f"<a href='{link(view='compare')}' target='_self'>Compare ({len(S.cmp)})</a>")
    links.append(f"<span class='chip'>{esc(S.country)} · {currency_short(S.cur)}</span>")
    return (f"<div class='topbar'><a class='logo' href='{link(view='home', tab='search', pid=None)}' target='_self'>"
            f"<span class='logo-mark'></span>SourceScan</a><div class='top-links'>{''.join(links)}</div></div>")


def band(key="band"):
    """The dark full-width band with the top bar. Use as `with band(): ...` to add content to it."""
    c = st.container(key=key)
    c.markdown(topbar_html(), unsafe_allow_html=True)
    return c


def nav_bar():
    """Top bar for inner pages."""
    band()


def sample_banner():
    st.markdown(tag("Delivered prices are estimates", "est"), unsafe_allow_html=True)


def scroll_to_top_on_view_change():
    view = f"{S.view}:{S.pid if S.view == 'detail' else ''}:{S.tab if S.view == 'home' else ''}"
    if S.get("_last_view") != view:
        S._last_view = view
        # run after the new page has rendered (Streamlit keeps the old scroll position otherwise)
        # (own scope: st.html scripts share the page's global scope; the view name makes the HTML
        # differ from page to page, otherwise Streamlit keeps the old element and the script won't rerun)
        st.html(f"<script data-view='{html.escape(view)}'>(() => {{ const up = () => {{"
                "const m = document.querySelector('[data-testid=\"stMain\"]');"
                "if (m) m.scrollTo(0, 0); window.scrollTo(0, 0); };"
                "setTimeout(up, 80); setTimeout(up, 400); })();</script>", unsafe_allow_javascript=True)


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
