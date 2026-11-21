"""Results: Amazon-style product list with delivered prices."""

import streamlit as st

from components.state import S, bound, go, link
from components.ui import (NA, band, currency_label, esc, fx_line_short, image_uri, money,
                           platform_search_url, platform_tag, tag, units)
from core import query_translation
from core.catalog import PLATFORMS, SELLER_TYPES, search
from core.pricing import COUNTRIES, CURRENCIES, SYMBOL, delivered
from core.supplier_score import score_colour, supplier_score
from views.live import live_search, with_buyer_details


# ---------------------------------------------------------------------------- AI query translation
class _PlanUnavailable(Exception):
    pass


@st.cache_data(ttl=24 * 3600, show_spinner=False, max_entries=500)
def _cached_plan(query):
    plan, reason = query_translation.plan_search(query)
    if plan is None:
        raise _PlanUnavailable(reason)  # failures are not cached, so a fixed key works at once
    return plan


def translated(query):
    """(plan, None) or (None, reason). One API call per distinct query per day."""
    if not query:
        return None, None
    try:
        return _cached_plan(query), None
    except _PlanUnavailable as e:
        return None, str(e)


def translation_strip(plan, reason, via_translation):
    """One quiet line under the search title; details fold out on tap."""
    if plan is None:
        if reason:
            st.markdown(f"<div class='muted' style='font-size:.8rem'>Chinese query: "
                        f"<span class='na'>{NA}</span> · {esc(reason)}</div>", unsafe_allow_html=True)
        return
    links = " · ".join(
        f"<a href='{platform_search_url(p, plan['query_zh'])}' target='_blank' rel='noopener'>{p} ↗</a>"
        for p in ("1688", "Taobao", "JD"))
    alts = " · ".join(esc(a) for a in plan["alternative_queries_zh"]) or NA
    tips = "".join(f"<li>{esc(c)}</li>" for c in plan["clarify"])
    matched = " · matched via translation" if via_translation else ""
    st.markdown(
        f"<details class='tr'><summary>Searched as <b>{esc(plan['query_zh'])}</b> "
        f"<span class='muted'>· {esc(plan['query_zh_meaning_en'])}{matched}</span></summary>"
        f"<div class='tr-in'>"
        f"<div>{esc(plan['pinyin'])} · {esc(plan['detected_language'])}</div>"
        f"<div>Intent: {esc(plan['intent_en'])}</div>"
        f"<div>Alternatives: {alts}</div>"
        f"<div>Search it live: {links}</div>"
        + (f"<div>To get better offers, tell suppliers:<ul>{tips}</ul></div>" if tips else "")
        + f"<div>{tag('AI translation — check before sending', 'est')}</div>"
        f"</div></details>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------- list
def enrich(products):
    rows = []
    for p in products:
        p = with_buyer_details(p)
        d = delivered(p, S.qty, S.country, S.cur)
        score, _ = supplier_score(p.get("supplier"))
        rows.append(dict(p=p, d=d, score=score, ok=d["per_unit"] is not None and not d["below_moq"]))
    return rows


def why_not(r):
    if r["d"]["below_moq"]:
        return f"Needs at least {units(r['p']['moq'])} (MOQ) — you asked for {S.qty:,}"
    return "Delivered price not available — the listing has no weight, so shipping can't be estimated"


def product_card(r, sym, top=False, saving=None):
    """Photo, English name, marketplace tag, supplier score, final delivered price.
    The whole card opens the product page."""
    p, d, score = r["p"], r["d"], r["score"]
    tags = [platform_tag(p.get("platform")),
            "<span class='src-tag live'>Live</span>" if p.get("live") else "<span class='src-tag'>Sample</span>",
            f"<span class='sc' style='background:{score_colour(score)}'>Supplier "
            f"{score if score is not None else 'n/a'}{'/100' if score is not None else ''}</span>"]
    if r["ok"]:
        price = f"<div class='pc-price'>{money(d['per_unit'], sym)}<small>/unit delivered</small></div>"
        moq = f"{p['moq']:,}" if p.get("moq") is not None else NA
        sub = (f"{money(d['total'], sym, 0)} for {units(S.qty)} · {d['mode_label']}, "
               f"{d['transit_days']} days · MOQ {moq}")
    elif p.get("live") and p.get("tiers"):
        shelf = sorted(p["tiers"])[0][1]
        price = f"<div class='pc-price'>¥{shelf:,.2f}<small>/unit on Yiwugo</small></div>"
        sub = ("Listing price, before shipping and tax. The listing has no weight: open it and add "
               "the weight to see the delivered price.")
    else:
        price = f"<div class='pc-na'>Delivered price {NA}</div>"
        sub = why_not(r)
    badges = ""
    if top:
        badges = "<span class='best-tag'>Best price</span>"
        if saving:
            badges += f"<span class='save'>Save {saving:.0f}%</span>"
    return (f"<a class='pc{' top' if top else ''}' href='{link(view='detail', pid=p['id'])}' target='_self'>"
            f"<img class='pc-img' src='{image_uri(p, square=True)}' alt=''/>"
            f"<div class='pc-body'>"
            f"<div class='pc-title'>{esc(p.get('title_en') or p.get('title_cn') or NA)}</div>"
            f"<div class='pc-meta'>{''.join(tags)}</div>"
            f"{price}"
            + (f"<div class='pc-meta'>{badges}</div>" if badges else "")
            + f"<div class='pc-sub'>{sub}</div>"
            f"</div></a>")


def _markets_on():
    """Marketplaces left on. All of them, until the buyer turns one off."""
    if "_w_markets" not in S:
        return list(PLATFORMS)
    return list(S._w_markets or [])


def _real_only():
    return bool(S.get("_w_real_only"))


def _market_label(name):
    return "Yiwugo · real" if name == "Yiwugo" else f"{name} · sample"


def page_results():
    sym = SYMBOL[S.cur]
    show = _markets_on()
    real_only = _real_only()
    plan, reason = None, None
    if S.q:
        with st.spinner("Translating your search for Chinese marketplaces…"):
            plan, reason = translated(S.q)
    base, via_translation = [], False
    if plan and plan["keywords_en"]:
        # the AI's English product keywords match the catalog better than raw text
        base = search(" ".join(plan["keywords_en"]))
        via_translation = bool(base) and plan["detected_language"].lower() != "english"
    if not base:
        base = search(S.q)
    # ---- header first (in the dark band), so the page shows something while Yiwugo answers
    budget_txt = f" · max {money(S.budget, sym)}/unit" if S.budget else ""
    with band():
        st.markdown(
            f"<a class='rh-back' href='{link(view='home', tab='search', pid=None)}' target='_self'>← New search</a>"
            f"<div class='rh-q'>“{esc(S.q) or 'All products'}”</div>"
            f"<div class='rh-sub'>{S.qty:,} units · to {S.country} · {S.cur}{budget_txt}</div>",
            unsafe_allow_html=True,
        )
        translation_strip(plan, reason, via_translation)
        with st.popover("Change quantity, country, currency", width="content"):
            bound(st.number_input, "Quantity", "qty", min_value=1, step=50)
            bound(st.selectbox, "Delivery country", "country", options=list(COUNTRIES))
            bound(st.selectbox, "Currency", "cur", options=CURRENCIES, format_func=currency_label)
            bound(st.number_input, f"Max budget per unit ({S.cur}, 0 = none)", "budget", min_value=0.0, step=0.5)
    pill_kw = dict(selection_mode="multi", format_func=_market_label, help=(
        "Turn a marketplace off to hide it. Yiwugo is read from the site. "
        "1688, Taobao and JD are sample data."))
    if "_w_markets" not in S:
        pill_kw["default"] = list(PLATFORMS)
    st.pills("Marketplaces", PLATFORMS, key="_w_markets", wrap=True, **pill_kw)
    st.toggle("Real listings only", key="_w_real_only",
              help="Hide the sample catalog and show only listings read from Yiwugo.")

    # ---- live Yiwugo listings
    live, live_err = [], None
    if "Yiwugo" in show and (S.q or "").strip():
        zh = ((plan or {}).get("query_zh") or S.q).strip()
        S.yiwugo_q = zh
        with st.spinner("Reading live Yiwugo listings…"):
            live, live_err = live_search(zh)
        if live:   # real Yiwugo listings replace the sample Yiwugo ones
            base = [item for item in base if item.get("platform") != "Yiwugo"] + live
    if live:
        st.markdown(f"<div class='muted' style='font-size:.8rem'><span class='src-tag live'>Live</span> "
                    f"{len(live)} listings read from yiwugo.com · other products: sample catalog</div>",
                    unsafe_allow_html=True)
    elif live_err and live_err != "off":
        st.markdown(f"<div class='muted' style='font-size:.8rem'>Live Yiwugo listings: <span class='na'>{NA}</span>"
                    f" · {esc(live_err)} · showing the sample catalog</div>", unsafe_allow_html=True)
    rows = enrich(base)

    # ---- sidebar filters (collapsed by default, out of the way on mobile)
    with st.sidebar:
        st.header("Filters")
        f_type = st.multiselect("Seller type", SELLER_TYPES, default=SELLER_TYPES,
                                format_func=lambda t: {"factory": "Factory", "store": "Store",
                                                       "middleman": "Middleman / trading co."}[t])
        f_score = st.slider("Minimum supplier score", 0, 100, 0, step=5)
        max_moq_all = max([r["p"]["moq"] or 0 for r in rows] + [1])
        f_moq = st.number_input("Maximum MOQ", min_value=1, value=int(max_moq_all), step=50)
        st.caption("Supplier score is a sample rule-based rating. Products with unknown score are kept "
                   "only when minimum score is 0.")

    def keep(r):
        p = r["p"]
        seller = p["supplier"].get("type")
        if p["platform"] not in show or (seller is not None and seller not in f_type):
            return False
        if real_only and not p.get("live"):
            return False
        if f_score > 0 and (r["score"] is None or r["score"] < f_score):
            return False
        return not (p["moq"] is not None and p["moq"] > f_moq)

    filtered = [r for r in rows if keep(r)]
    over_budget = []
    if S.budget:
        over_budget = [r for r in filtered if r["ok"] and r["d"]["per_unit"] > S.budget]
        filtered = [r for r in filtered if r not in over_budget]

    if not show:
        st.info("All marketplaces are off. Turn one on to see products.")
        return
    if real_only and not any(r["p"].get("live") for r in filtered):
        st.info("No real listings for this search. Only Yiwugo is read from the site right now.")
        return
    if not base:
        st.warning(f"No products in the sample catalog match “{S.q}”. "
                   "Try tote bag, water bottle, phone case, yoga mat, mug or LED strip.")
        return
    if not filtered:
        st.info("No results match the current filters or budget.")
        return

    # ---- count + sort, side by side even on a phone
    c_count, c_sort = st.columns([1, 1.25])
    with c_count:
        st.markdown("<span class='nowrap'></span>", unsafe_allow_html=True)
        st.markdown(f"<div class='list-count'>{len(filtered)} products"
                    + (f" · {len(over_budget)} over budget hidden" if over_budget else "") + "</div>",
                    unsafe_allow_html=True)
    with c_sort:
        sort = st.selectbox("Sort by", ["Lowest price", "Best supplier score", "Lowest MOQ"],
                            label_visibility="collapsed")
    big = 10 ** 12
    keyfn = {
        "Lowest price": lambda r: r["d"]["per_unit"],
        "Best supplier score": lambda r: -(r["score"] if r["score"] is not None else -1),
        "Lowest MOQ": lambda r: r["p"]["moq"] if r["p"]["moq"] is not None else big,
    }[sort]
    # products without a delivered price at this quantity always go last
    priced = sorted((r for r in filtered if r["ok"]), key=keyfn)
    unpriced = [r for r in filtered if not r["ok"]]
    if sort == "Lowest price":   # live listings without a delivered price: by the listing price shown
        unpriced.sort(key=lambda r: sorted(r["p"]["tiers"])[0][1]
                      if r["p"].get("live") and r["p"].get("tiers") else big)
    else:
        unpriced.sort(key=keyfn)
    best = min(priced, key=lambda r: r["d"]["per_unit"], default=None)
    saving = None
    if best and len(priced) > 1:
        hi = max(r["d"]["per_unit"] for r in priced)
        saving = (hi - best["d"]["per_unit"]) / hi * 100 if hi > 0 else None

    st.markdown(
        "<div class='plist'>"
        + "".join(product_card(r, sym, top=r is best, saving=saving) for r in priced + unpriced)
        + "</div>"
        f"<div class='foot'>Prices include shipping (cheapest method for {S.qty:,} units), duty, VAT and "
        f"customs, estimated · {fx_line_short()} · Supplier scores are sample values for now · "
        + ("Live = listing read from yiwugo.com, Sample = demo catalog" if live else "Sample catalog")
        + "</div>",
        unsafe_allow_html=True,
    )

    with st.expander("Compare products"):
        opts = {r["p"]["id"]: f"{r['p']['platform']} · {(r['p'].get('title_en') or r['p'].get('title_cn') or NA)[:40]}"
                for r in filtered}
        picked = st.multiselect("Pick 2–3 products", list(opts), default=[x for x in S.cmp if x in opts],
                                format_func=opts.get, max_selections=3)
        if st.button("Compare", disabled=len(picked) < 2):
            go("compare", cmp=picked)
            st.rerun()
