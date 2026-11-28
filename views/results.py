"""Results: three cards per row (one on phones), each with the photo, the name, the final delivered
price and the final trust score. All the details are on the product page."""

import streamlit as st

from components.state import S, bound, go, link
from components.ui import (NA, currency_label, demo_tag, esc, fx_line_short, image_uri, money, pagehero,
                           platform_search_url, tag, trust_pill, units)
from core import query_translation
from core.catalog import PLATFORMS, SELLER_TYPES, search
from core.pricing import COUNTRIES, CURRENCIES, SYMBOL, delivered
from core.scoring import COUNTERFEIT_REASON
from core.supplier_score import trust_for_search

SORTS = ["Most trusted", "Lowest price", "Lowest MOQ"]


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


def search_base(q, plan):
    """The products of a search: (products, matched_via_translation). The AI's English keywords
    match the catalog better than raw text; the raw query is the fallback."""
    if plan and plan["keywords_en"]:
        base = search(" ".join(plan["keywords_en"]))
        if base:
            return base, plan["detected_language"].lower() != "english"
    return search(q), False


def trust_in_search(p, q=None):
    """p's trust score in the context of a search (sales and prices are compared with the other
    results of the same platform), so the product page shows the same score as the list.
    q = None: the current search; q = "": the whole catalog (Link analyzer).
    None when p is not part of the search."""
    q = S.q if q is None else q
    plan = translated(q)[0] if q else None
    base, _ = search_base(q, plan)
    if p["id"] not in {x["id"] for x in base}:
        return None
    return trust_for_search([(x, delivered(x, S.qty, S.country, S.cur)["unit_cny"]) for x in base])[p["id"]]


def translation_strip(plan, reason, via_translation):
    """One quiet line under the search title; details fold out on tap. Nothing when there is no translation."""
    if plan is None:
        return
    links = " · ".join(
        f"<a href='{platform_search_url(p, plan['query_zh'])}' target='_blank' rel='noopener'>{p} ↗</a>"
        for p in PLATFORMS)
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
        d = delivered(p, S.qty, S.country, S.cur)
        rows.append(dict(p=p, d=d, ok=d["per_unit"] is not None and not d["below_moq"]))
    # one trust calculation for the whole search: sales and prices compared within the same platform
    trust = trust_for_search([(r["p"], r["d"]["unit_cny"]) for r in rows])
    for r in rows:
        r["trust"] = trust[r["p"]["id"]]
        r["score"] = r["trust"]["score"]
    return rows


def why_not(r):
    if r["d"]["below_moq"]:
        return f"Needs at least {units(r['p']['moq'])} (MOQ) — you asked for {S.qty:,}"
    return "Delivered price not available — the listing has no weight, so shipping can't be estimated"


def product_card(r, sym):
    """Photo, name, final delivered price and final trust score; everything else is on the product page,
    which the whole card opens. The photo carries the 'demo data' and counterfeit-risk labels."""
    p, d = r["p"], r["d"]
    flags = demo_tag(p)
    if COUNTERFEIT_REASON in r["trust"]["penalties"]:
        flags += "<span class='warn-tag'>⚠ Possible counterfeit</span>"
    if r["ok"]:
        price = (f"<span class='gc-price'>{money(d['per_unit'], sym)}</span>"
                 f"<span class='gc-unit'>per unit, delivered to {esc(S.country)}</span>")
    else:
        price = (f"<span class='gc-price na-price'>{NA}</span><span class='gc-unit'>{esc(why_not(r))}</span>")
    return (f"<a class='gc' href='{link(view='detail', pid=p['id'])}' target='_self'>"
            f"<span class='gc-media'><img src='{image_uri(p, square=True)}' alt=''/>"
            f"<span class='gc-flags'>{flags}</span></span>"
            f"<span class='gc-body'><span class='gc-title'>{esc(p.get('title_en') or p.get('title_cn') or NA)}</span>"
            f"<span class='gc-row'><span class='gc-l'>Final price</span>{price}</span>"
            f"<span class='gc-row'><span class='gc-l'>Final trust score</span>{trust_pill(r['trust'], big=True)}</span>"
            f"</span></a>")


def page_results():
    sym = SYMBOL[S.cur]
    plan, reason = None, None
    if S.q:
        with st.spinner("Translating your search for Chinese marketplaces…"):
            plan, reason = translated(S.q)
    base, via_translation = search_base(S.q, plan)
    budget_txt = f" · max {money(S.budget, sym)}/unit" if S.budget else ""
    st.markdown(pagehero("Results", f"“{esc(S.q) or 'All products'}”",
                         f"{S.qty:,} units · delivered to {esc(S.country)} · {S.cur}{budget_txt}", steps=1,
                         compact=True), unsafe_allow_html=True)
    with st.container(key="rtools"):
        translation_strip(plan, reason, via_translation)
        with st.popover("Change quantity, country, currency", width="content"):
            bound(st.number_input, "Quantity", "qty", min_value=1, step=50)
            bound(st.selectbox, "Delivery country", "country", options=list(COUNTRIES))
            bound(st.selectbox, "Currency", "cur", options=CURRENCIES, format_func=currency_label)
            bound(st.number_input, f"Max budget per unit ({S.cur}, 0 = none)", "budget", min_value=0.0, step=0.5)

    rows = enrich(base)

    # ---- sidebar filters (collapsed by default, out of the way on mobile)
    with st.sidebar:
        st.header("Filters")
        f_platform = st.multiselect("Platform", PLATFORMS, default=PLATFORMS)
        f_type = st.multiselect("Seller type", SELLER_TYPES, default=SELLER_TYPES,
                                format_func=lambda t: {"factory": "Factory", "brand_official": "Brand official store",
                                                       "authorized_store": "Authorized store",
                                                       "trader": "Trader / trading co."}[t])
        f_score = st.slider("Minimum trust score", 0, 100, 0, step=5)
        max_moq_all = max([r["p"]["moq"] or 0 for r in rows] + [1])
        f_moq = st.number_input("Maximum MOQ", min_value=1, value=int(max_moq_all), step=50)
        st.caption("The trust score sums up public signals (see “How we score” on any product page). "
                   "Sellers with not enough data are kept only when the minimum is 0.")

    def keep(r):
        p = r["p"]
        seller = p["supplier"].get("type")
        if p["platform"] not in f_platform or (seller is not None and seller not in f_type):
            return False
        if f_score > 0 and (r["score"] is None or r["score"] < f_score):
            return False
        return not (p["moq"] is not None and p["moq"] > f_moq)

    filtered = [r for r in rows if keep(r)]
    over_budget = []
    if S.budget:
        over_budget = [r for r in filtered if r["ok"] and r["d"]["per_unit"] > S.budget]
        filtered = [r for r in filtered if r not in over_budget]

    if not base:
        st.warning(f"No products in our catalog match “{S.q}”. The demo catalog has padel rackets: "
                   "try padel racket, carbon or beginner.")
        return
    if not filtered:
        st.info("No results match the current filters or budget.")
        return

    # ---- sort chips + count
    c_sort, c_count = st.columns([2, 1], vertical_alignment="center")
    with c_sort:
        if S.get("sort") not in SORTS:
            S.sort = SORTS[0]
        sort = st.segmented_control("Sort by", SORTS, key="sort", required=True, label_visibility="collapsed")
    with c_count:
        st.markdown(f"<div class='list-count'>{len(filtered)} suppliers"
                    + (f" · {len(over_budget)} over budget hidden" if over_budget else "") + "</div>",
                    unsafe_allow_html=True)
    big = 10 ** 12
    keyfn = {
        "Lowest price": lambda r: r["d"]["per_unit"],
        # most trusted first; same score -> cheaper delivered price first
        "Most trusted": lambda r: (-(r["score"] if r["score"] is not None else -1),
                                   r["d"]["per_unit"] if r["ok"] else big),
        "Lowest MOQ": lambda r: r["p"]["moq"] if r["p"]["moq"] is not None else big,
    }[sort]
    # products without a delivered price at this quantity always go last
    priced = sorted((r for r in filtered if r["ok"]), key=keyfn)
    unpriced = sorted((r for r in filtered if not r["ok"]),
                      key=keyfn if sort != "Lowest price" else (lambda r: big))
    st.markdown(
        "<div class='grid'>"
        + "".join(product_card(r, sym) for r in priced + unpriced)
        + "</div>"
        f"<div class='foot'>Prices include shipping (cheapest method for {S.qty:,} units), duty, VAT and "
        f"customs, estimated · {fx_line_short()} · Trust scores sum up public signals, not an official "
        f"verification · “demo data” = listing with some made-up values</div>",
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
