"""Link analyzer: paste a marketplace link and get the full product page, with the same sections and
the same trust metrics as a product opened from the search.

For now it works with the listings of our catalog (data/catalog_merged.json): the link is matched to
a catalog product, ignoring tracking parameters and the variant id. Marketplace pages are never
fetched. The analysed product is kept in the address (pid), so a reload shows it again.
"""

import streamlit as st

from components.state import S
from components.ui import esc, pagehero
from core.catalog import find_by_url, get_product, platform_from_url
from views.product import render_detail

SAMPLE_PID = "8"          # the example link


def _analyze():
    url = (S.get("la_url") or "").strip()
    S.la_error = None
    if not url:
        S.pid, S.la_error = None, "empty"
        return
    p = find_by_url(url)
    if p:
        S.pid = p["id"]
    else:
        S.pid, S.la_error = None, platform_from_url(url) or "unknown"


def _use_sample():
    S.la_url = get_product(SAMPLE_PID)["url"]
    _analyze()


def page_link():
    st.markdown(pagehero("Link analyzer", "Paste a link. Get the full picture.",
                         "A listing from 1688, Taobao, JD or Pinduoduo: product, delivered price, trust score "
                         "with all its metrics, and the supplier, exactly as in the search."), unsafe_allow_html=True)
    if S.pop("la_auto", False):               # a link typed in the home search box
        _analyze()
    with st.container(key="panel"):
        c_url, c_go = st.columns([4, 1], vertical_alignment="bottom")
        c_url.text_input("Listing link", key="la_url", placeholder="https://detail.1688.com/offer/…")
        c_go.button("Analyze →", type="primary", on_click=_analyze, width="stretch", key="la_go")
        st.button("Try an example link", type="tertiary", on_click=_use_sample)

    err = S.get("la_error")
    if err == "empty":
        st.warning("Paste a listing link first.")
    elif err:
        where = f" on {err}" if err != "unknown" else ""
        st.info(f"We can't analyse this listing{where} yet. Check the link, or try another listing.")
    p = get_product(S.pid) if S.view == "link" and S.pid else None
    if p:
        st.success(f"Found: {esc(p.get('title_en') or p.get('title_cn') or '')} on {p.get('platform')}.")
        # same sections as the product page; trust compared with the whole catalog, like a search for it
        render_detail(p, "catalog", trust_q="")
