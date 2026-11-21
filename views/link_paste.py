"""Link paste: paste a marketplace link (and, if needed, a screenshot or the page text)
and get the same analysis as a product page.

- a link to a product in our catalog -> its full product page at once
- any other link -> we ask for a screenshot or the page text and the AI reads it
  (marketplace pages are never fetched: they block bots and scraping breaks their terms)
"""

import streamlit as st

from components.ui import tag
from core import listing
from core.catalog import PRODUCTS, find_by_url, get_product
from core.pricing import DUTY
from components.state import S
from views.product import render_detail

FIELDS = ["title_cn", "platform", "moq", "material", "size", "weight_kg", "production_days"]


def _use_sample_link():
    S.lp_url = PRODUCTS[0]["url"]


def _use_sample_text():
    S.lp_text = listing.SAMPLE_LISTING


def _analyze():
    url = (S.get("lp_url") or "").strip()
    text = (S.get("lp_text") or "").strip()
    shot = S.get("lp_img")
    if not (url or text or shot):
        S.lp_result = {"kind": "empty"}
        return
    p = find_by_url(url) if url else None
    if p:
        S.lp_result = {"kind": "catalog", "pid": p["id"]}
        return
    if shot is None and not text:
        S.lp_result = {"kind": "need_more", "platform": listing.platform_from_url(url)}
        return
    image = shot.getvalue() if shot is not None else None
    card, err = listing.read_listing(text=text or None, image=image,
                                     media_type=getattr(shot, "type", None), url=url or None)
    if card is not None:
        S.lp_result = {"kind": "read", "card": card, "source": "screenshot" if image else "text"}
    elif text:
        card = listing.parse_listing(text)
        if url:
            card["url"] = url
            card["platform"] = card.get("platform") or listing.platform_from_url(url)
        S.lp_result = {"kind": "read", "card": card, "source": "text",
                       "note": f"AI reading not available ({err}), read with basic rules: fewer fields, "
                               "approximate translation."}
    else:
        S.lp_result = {"kind": "error", "msg": f"Could not read the screenshot — {err}"}


def render_link_form():
    """The input part (shown in the dark band on the home page)."""
    c_url, c_go = st.columns([4, 1])
    with c_url:
        st.text_input("Paste a link", key="lp_url", placeholder="https://detail.1688.com/offer/…")
    with c_go:
        st.button("Analyze", type="primary", on_click=_analyze, width="stretch", key="lp_go")
    st.button("Try a sample link", type="tertiary", on_click=_use_sample_link)
    st.file_uploader("Screenshot of the listing (optional)", type=["png", "jpg", "jpeg", "webp"], key="lp_img",
                     help="Needed for links outside our catalog: we read the page from your screenshot.")
    with st.expander("…or paste the page text"):
        st.text_area("Page text", key="lp_text", height=180, label_visibility="collapsed",
                     placeholder="Copy the title, prices, MOQ, specs and shop info from the page")
        st.button("Use an example listing", on_click=_use_sample_text)


def render_link_paste():
    render_link_form()
    render_link_result()


def render_link_result():
    """The analysis (shown below the band)."""
    r = S.get("lp_result")
    if not r:
        return
    if r["kind"] == "empty":
        st.warning("Paste a link, a screenshot or the page text first.")
    elif r["kind"] == "error":
        st.error(r["msg"])
    elif r["kind"] == "need_more":
        where = f" on {r['platform']}" if r.get("platform") else ""
        st.info(f"Got the link{where}. We don't open marketplace pages ourselves (they block automated "
                "access, and copying them breaks their terms), so add a **screenshot** of the page or paste "
                "its **text** above, then tap Analyze again.")
    elif r["kind"] == "catalog":
        p = get_product(r["pid"])
        st.success("Found in our catalog — full analysis below.")
        render_detail(p, "catalog")
    elif r["kind"] == "read":
        _render_read(r)


def _render_read(r):
    p = dict(r["card"])
    found = sum(1 for k in FIELDS if p.get(k) is not None) + (1 if p.get("tiers") else 0)
    st.success(f"Listing read from your {r['source']} — {found} of 8 key product fields found.")
    if r.get("note"):
        st.caption(r["note"])
    with st.expander("Add details we could not find (optional)",
                     expanded=p.get("weight_kg") is None or p.get("category") is None):
        st.caption("Values you enter here are marked as user-provided and used for the delivered price.")
        c1, c2 = st.columns(2)
        w = c1.number_input("Weight per unit (g)", min_value=0, value=int((p.get("weight_kg") or 0) * 1000),
                            step=10, key="lp_weight")
        cats = ["(not set)"] + list(DUTY)
        cat = c2.selectbox("Product category (for duty rate)", cats, key="lp_cat",
                           index=cats.index(p["category"]) if p.get("category") in cats else 0)
    new_w = w / 1000 if w > 0 else None
    if new_w != p.get("weight_kg"):
        p["weight_kg"], p["weight_user"] = new_w, new_w is not None
    p["category"] = None if cat == "(not set)" else cat
    if not p.get("title_en") and not p.get("tiers"):
        st.markdown(tag("Very little found", "na") + "<span class='muted'>Try a sharper screenshot that shows "
                    "the title and the price table.</span>", unsafe_allow_html=True)
    render_detail(p, r["source"])
