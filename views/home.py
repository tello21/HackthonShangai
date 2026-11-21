"""Home: a dark band with the top bar, pill tabs — Link paste · Sourcing (default) · Messages —
a headline and the tab's input; results of the tab below the band."""

import streamlit as st

from components import style
from components.state import S, TABS, go, link
from components.ui import band, currency_short, unread_count
from core.pricing import COUNTRIES, CURRENCIES
from views.faq import faq_html
from views.link_paste import render_link_form, render_link_result
from views.messages import render_inbox

HEADLINES = {
    "search": "Find trusted suppliers in China. See the real price, delivered.",
    "link": "Paste a link. Get the real price.",
    "messages": "Your suppliers, in your language.",
}


HOW_IT_WORKS = (
    "<div class='how'>"
    "<div class='how-card'><div class='how-n'>1</div><div class='how-t'>Search in your language</div>"
    "<div class='how-d'>We turn it into the words Chinese sellers use and look on 1688, Taobao, JD and Pinduoduo."
    "</div></div>"
    "<div class='how-card'><div class='how-n'>2</div><div class='how-t'>See the delivered price</div>"
    "<div class='how-d'>Product, shipping, duty, VAT and customs to your country, at today's ECB rate."
    "</div></div>"
    "<div class='how-card'><div class='how-n'>3</div><div class='how-t'>Know who you're buying from</div>"
    "<div class='how-d'>Every seller gets a trust score with the reasons behind it: factory or trader, years "
    "active, verified badges, response and dispute history.</div></div></div>"
)


def _tab_label(t):
    n = unread_count()
    return {"link": "🔗 Link paste", "search": "🔎 Sourcing",
            "messages": f"💬 Messages{f' ({n})' if n else ''}"}[t]


def _tab_changed():
    if S.get("home_tab"):
        S.tab = S.home_tab


def search_bar():
    """One horizontal bar: what · quantity · deliver to · currency · Search (stacks on phones)."""
    with st.form("search_form", border=False):
        c_q, c_qty, c_country, c_cur, c_go = st.columns([2.6, 0.9, 1.3, 0.9, 1], gap="small")
        query = c_q.text_input("What are you looking for?", value=S.q,
                               placeholder="e.g. carbon padel racket…")
        qty = c_qty.number_input("Quantity", min_value=1, value=int(S.qty), step=50)
        countries = list(COUNTRIES)
        country = c_country.selectbox("Deliver to", countries, index=countries.index(S.country))
        cur = c_cur.selectbox("Currency", CURRENCIES, index=CURRENCIES.index(S.cur), format_func=currency_short)
        submitted = c_go.form_submit_button("Search", type="primary", width="stretch")
    if submitted:
        go("results", q=query.strip(), qty=int(qty), country=country, cur=cur or S.cur, pid=None, cmp=[])
        st.rerun()
    st.markdown("<div class='hero-foot'>Searching 1688 · Taobao · JD · Pinduoduo · every seller with a trust score"
                "</div>", unsafe_allow_html=True)


def page_home():
    style.inject_home()
    with band("hero"):
        S["home_tab"] = S.tab
        st.segmented_control("Section", list(TABS), key="home_tab", format_func=_tab_label, required=True,
                             on_change=_tab_changed, label_visibility="collapsed", width="stretch")
        st.markdown(f"<div class='hero-title'>{HEADLINES[S.tab]}</div>", unsafe_allow_html=True)
        if S.tab == "search":
            search_bar()
        elif S.tab == "link":
            st.markdown("<div class='hero-sub'>From 1688, Taobao, JD or Pinduoduo: product, delivered price and "
                        "supplier in one page.</div>", unsafe_allow_html=True)
            render_link_form()
        else:
            st.markdown("<div class='hero-sub'>You write in your language, they read Chinese.</div>",
                        unsafe_allow_html=True)

    if S.tab == "search":
        st.markdown(HOW_IT_WORKS, unsafe_allow_html=True)
        st.markdown(faq_html(), unsafe_allow_html=True)
    elif S.tab == "link":
        render_link_result()
    elif S.tab == "messages":
        render_inbox()
        if S.orders:
            st.markdown(f"<a href='{link(view='orders', order=None)}' target='_self'>📦 Your orders "
                        f"({len(S.orders)})</a>", unsafe_allow_html=True)
