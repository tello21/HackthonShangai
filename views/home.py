"""Home, after the team's mock-up: top bar, centred hero with the search panel, the six steps,
"Trust, explained" (the real scoring rules, per marketplace), the FAQ and a closing call to action."""

import streamlit as st

from components import style
from components.state import S, go, link
from components.ui import band, currency_short, esc, trust_pill  # noqa: F401
from core.catalog import PLATFORMS, PRODUCTS
from core.pricing import COUNTRIES, CURRENCIES, delivered
from core.supplier_score import trust_for_search
from views.faq import faq_html, metrics_html, rules_html

STEPS = [
    ("Search across China",
     "Find products from 1688, Taobao, JD and Pinduoduo in your own language. We translate your words "
     "into the ones Chinese sellers use."),
    ("Compare products and suppliers",
     "Every result shows the photo, the final delivered price and the final trust score; open it for specs, "
     "price tiers, MOQ and all the seller details."),
    ("Check supplier trust",
     "A rules-based score from public badges, store history, customer feedback, repurchase rate and sales. "
     "Missing evidence is shown, never hidden; red flags cost points."),
    ("See the full delivered cost",
     "Product price for your quantity, ECB exchange rate, international shipping, insurance, customs duty, "
     "clearance and import VAT in one estimated landed total."),
    ("Message the supplier",
     "Write in your language: the supplier reads natural business Chinese, and replies come back translated "
     "and explained, with the deal terms collected for you."),
    ("Choose and buy",
     "Order from the product page or at the price agreed in chat: 30% deposit, 70% balance before shipping, "
     "with order tracking. Payments are simulated in this demo."),
]


def search_panel():
    """One white panel: what · quantity · deliver to · currency · Search suppliers.
    The product field always starts empty: the buyer types the search."""
    with st.container(key="searchpanel"):
        with st.form("search_form", border=False):
            c_q, c_qty, c_country, c_cur, c_go = st.columns([2.4, 0.8, 1, 0.9, 1.1], gap="small",
                                                           vertical_alignment="bottom")
            query = c_q.text_input("Product", value="", placeholder="e.g. padel racket")
            qty = c_qty.number_input("Quantity", min_value=1, value=int(S.qty), step=50)
            countries = list(COUNTRIES)
            country = c_country.selectbox("Deliver to", countries, index=countries.index(S.country))
            cur = c_cur.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(S.cur), format_func=currency_short)
            submitted = c_go.form_submit_button("Search suppliers →", type="primary", width="stretch")
    if submitted:
        q = query.strip()
        S.qty, S.country, S.cur = int(qty), country, cur or S.cur
        go("results", q=q, pid=None, cmp=[])
        st.rerun()


def _catalog_examples(platform):
    """The real catalog listings of one marketplace with their scores (all listings as one search)."""
    rows = [(p, delivered(p, S.qty, S.country, S.cur)["unit_cny"]) for p in PRODUCTS]
    trust = trust_for_search(rows)
    mine = [p for p, _ in rows if p["platform"] == platform]
    if not mine:
        return ""
    chips = "".join(f"<a href='{link(view='detail', pid=p['id'], q='')}' target='_self'>"
                    f"{esc((p['supplier'].get('name') or p['supplier'].get('name_cn') or '')[:28])} "
                    f"{trust_pill(trust[p['id']])}</a>" for p in mine)
    return (f"<div class='note'><b>In our catalog on {platform}:</b> {len(mine)} listing"
            f"{'' if len(mine) == 1 else 's'} (scored together, at {S.qty:,} units).</div><div class='ex'>{chips}</div>")


def trust_section():
    with st.container(key="trustsec"):
        left, right = st.columns([1, 1.08], gap="large")
        with left:
            st.markdown("<div class='sectiontag'>Trust, explained</div><div class='h2'>See the evidence.<br/>"
                        "Not just a badge.</div><p class='lead'>Our Python rules turn each marketplace's public "
                        "signals into one 0–100 score you can compare across platforms. Pick a marketplace to see "
                        "exactly what we read there and how it is scored.</p>" + rules_html(),
                        unsafe_allow_html=True)
        with right, st.container(key="scorebox"):
            st.markdown("<div class='scorehead'><div><div class='sectiontag'>How we score</div>"
                        "<div class='disp'>The six metrics</div></div>"
                        "<span class='samplechip'>Rules-based · no AI scoring</span></div>", unsafe_allow_html=True)
            if S.get("mk_pick") not in PLATFORMS:
                S.mk_pick = PLATFORMS[0]
            platform = st.segmented_control("Marketplace", PLATFORMS, key="mk_pick", required=True,
                                            label_visibility="collapsed", width="stretch")
            st.markdown(metrics_html(platform) + "<div class='note'>Bars show each metric's weight. A metric the "
                        "listing doesn't show counts as 50; under 40% coverage there is no score.</div>"
                        + _catalog_examples(platform), unsafe_allow_html=True)


def page_home():
    style.inject_home()
    band("hero")
    st.markdown("<div class='hero'><div class='hero-h1'>Search. Compare.<br/><span class='hl'>Trust. Buy.</span>"
                "</div><div class='hero-sub'>Discover products from Chinese suppliers, compare their public trust "
                "signals, see the full estimated cost to Europe and order through one streamlined checkout.</div>"
                "</div>", unsafe_allow_html=True)
    search_panel()
    st.markdown("<div class='markets'><span>Chinese marketplaces</span>"
                + "".join(f"<span class='market'>{p}</span>" for p in PLATFORMS)
                + "</div><div class='micro'>Translation · Supplier trust score · Shipping · VAT &amp; customs · "
                "All-in pricing · Checkout</div><div style='height:56px'></div>", unsafe_allow_html=True)

    st.markdown("<div class='fullbleed'><div class='sec'><div class='sectionhead'><div class='sectiontag'>"
                "Everything you need</div><div class='h2'>From search to checkout. All in one place.</div>"
                "<p class='lead'>Six simple steps connect European buyers to Chinese suppliers, with the "
                "information you need to compare, choose and order confidently.</p></div><div class='steps'>"
                + "".join(f"<div class='step'><span class='stepno'>{i:02d}</span><div class='step-t'>{esc(t)}</div>"
                          f"<p>{esc(d)}</p></div>" for i, (t, d) in enumerate(STEPS, 1))
                + "</div></div></div>", unsafe_allow_html=True)
    trust_section()
    st.markdown(faq_html(), unsafe_allow_html=True)
    st.markdown(f"<div class='endcta'><div class='endcta-h'>Find the product. Know the full picture.</div>"
                f"<p>From the Chinese supplier to your European doorstep: one simple buying journey.</p>"
                f"<a class='cta' href='{link(view='home', tab='search', pid=None)}' target='_self'>"
                f"Start searching ↑</a></div>", unsafe_allow_html=True)
