"""Product page: product card, delivered price, supplier, contact + order."""

import streamlit as st

from components.state import S, go
from components.ui import (NA, cny, demo_tag, esc, fact_grid, fx_line, image_uri, platform_tag, receipt, sample_banner,
                           search_link, section, tag, tier_cards, trust_bars, trust_pill, units)
from core import messages as M
from core.catalog import get_product, platform_from_url
from core.pricing import COUNTRIES, MODE_LABEL, SYMBOL, TRANSIT_DAYS, compare_modes, delivered
from core.scoring import BADGE_EN, PENALTY_POINTS, STORE_TYPES
from core.supplier_score import raw_fields, trust_for
from views.faq import how_we_score_html
from views.results import trust_in_search


def open_conversation(p, qty, country):
    """Contact supplier: open the existing chat for this product, or start one with the
    product, quantity, country and delivered price loaded as context."""
    # reuse only a chat that is still empty: once messages were exchanged, Contact supplier starts a
    # fresh chat with the message ready to send (the old one stays in Messages)
    existing = next((c for c in S.convs.values()
                     if c["pid"] == p["id"] and c.get("product") == p.get("title_en") and not c["messages"]), None)
    if existing:
        conv = existing
    else:
        d = delivered(p, qty, country, S.cur)
        conv = M.new_conversation(p, qty, country, S.cur, d["per_unit"])
        conv["card"] = dict(p)  # product card snapshot (pasted listings too)
        S.convs[conv["id"]] = conv
        M.save_conversations(S.convs)
    # the "Ask for quote" message is ready to send (also in a chat reopened from another session)
    S.setdefault(f"draft_{conv['id']}", M.quick_action_text("Ask for quote", qty, country, p.get("moq")))
    go("chat", conv=conv["id"])


def start_checkout(p, qty, country, mode, unit_price_cny=None, conv_id=None):
    """Open the checkout with this product; unit_price_cny = a price negotiated in chat."""
    S.checkout = {"card": dict(p), "qty": qty, "country": country, "mode": mode,
                  "unit_price_cny": unit_price_cny, "conv": conv_id}
    go("checkout")


def delivered_lines(d, qty):
    """The receipt lines for a delivered() result."""
    if d["duty_pct"] is None:
        duty_lbl, duty_basis = "Import duty", "rate not available for this product category"
    else:
        duty_lbl = f"Import duty ({d['duty_pct']:g}%)"
        duty_basis = "on product value" if d["duty_on_goods_only"] else "on product + shipping + insurance"
    kg = f"{d['charged_kg']:,.1f} kg chargeable" if d["charged_kg"] is not None else "needs weight — not available"
    return [
        ("Product", d["product"], f"{cny(d['unit_cny'])}/unit × {qty:,}"),
        (f"Shipping · {d['mode_label']}", d["shipping"], f"{kg} + China domestic transport"),
        ("Insurance (0.5%)", d["insurance"], "of product value"),
        (duty_lbl, d["duty"], duty_basis),
        ("Customs clearance", d["clearance"],
         "included by the courier" if d["clearance"] == 0 else "broker fee per shipment"),
        (f"{d['tax_name']} ({d['vat_pct']:g}%)" if d["vat_pct"] else d["tax_name"], d["vat"],
         "on all of the above" if d["vat_pct"] else ""),
    ]


def render_detail(p, source="catalog", trust_q=None):
    """The full product page. trust_q = the search whose results the trust score is compared with
    (None = the current search, "" = the whole catalog, as in Link analyzer)."""
    key = p["id"]
    s = p.get("supplier") or {}

    # ---- 1. Product sheet: photo + title + key numbers, then specs as tiles, then price tiers
    st.markdown(section(1, "Product"), unsafe_allow_html=True)
    tags = [platform_tag(p.get("platform")), demo_tag(p)]
    if p.get("counterfeit_risk"):
        tags.append(f"<span class='warn-tag'>⚠ Possible counterfeit brand</span>")
    if source != "catalog":
        tags.append(tag(f"Read from your {source}", "est"))
    if p.get("title_en_source") == "ai":
        tags.append(tag("English name translated by AI", "est"))
    elif source != "catalog" and p.get("title_en"):
        tags.append(tag("Translated title — approximate", "est"))
    orig = (f"<div class='ps-orig'>Original title · {esc(p['title_cn'])}</div>"
            if p.get("title_cn") and p.get("title_en") else "")

    def key_fact(label, value, unit=""):
        v = (f"{value}<small>{unit}</small>" if value is not None else f"<span class='na'>{NA}</span>")
        return f"<div class='kf'><div class='kf-v'>{v}</div><div class='kf-l'>{label}</div></div>"

    weight = f"{p['weight_kg'] * 1000:,.0f}" if p.get("weight_kg") is not None else None
    moq = f"{p['moq']:,}" if p.get("moq") is not None else None
    st.markdown(
        f"<div class='ps'><img class='ps-img' src='{image_uri(p, square=True)}' alt=''/>"
        f"<div class='ps-info'><div class='ps-tags'>{''.join(tags)}</div>"
        f"<div class='ps-title'>{esc(p.get('title_en') or p.get('title_cn') or NA)}</div>{orig}"
        f"<div class='kfs'>{key_fact('Minimum order', moq, ' units')}"
        f"{key_fact('Weight incl. packaging' if p.get('weight_includes_packaging') else 'Weight per unit', weight, ' g')}"
        f"{key_fact('Lead time', p.get('production_days'), ' days')}</div></div></div>",
        unsafe_allow_html=True)
    st.markdown(fact_grid([
        ("Material", esc(p.get("material")) or None),
        ("Size", esc(p.get("size")) or None),
        ("Customisation", esc(p.get("customisation")) or None, True),
    ]), unsafe_allow_html=True)
    if p.get("notes"):
        with st.expander("About this data" + (" · includes demo values" if p.get("demo") else "")):
            st.markdown(esc(p["notes"]))
    st.markdown("<div class='sub-h'>Price per unit by quantity <span>as listed by the seller</span></div>",
                unsafe_allow_html=True)
    if p.get("tiers"):
        # follows the quantity field of section 2 (its value from the previous run)
        st.markdown(tier_cards(p["tiers"], int(S.get(f"qty_{key}") or S.qty), S.cur), unsafe_allow_html=True)
        st.caption(fx_line(S.cur))
    else:
        st.markdown(f"<span class='na'>{NA}</span>", unsafe_allow_html=True)

    # ---- 2. Delivered price
    st.markdown(section(2, "Delivered price"), unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2 = st.columns([1, 1.3])
        qty = c1.number_input("Quantity", min_value=1, value=int(S.qty), step=50, key=f"qty_{key}")
        countries = list(COUNTRIES)
        country = c2.selectbox("Delivery country", countries, index=countries.index(S.country),
                               key=f"country_{key}")
        sym = SYMBOL[S.cur]

        # shipping method: cheapest first, each with its transit time and price
        by_mode = {d["mode"]: d for d in compare_modes(p, qty, country, S.cur)}

        def mode_name(m):
            d_ = by_mode[m]
            price = f"{sym}{d_['per_unit']:,.2f}/unit" if d_["per_unit"] is not None else NA
            return f"{MODE_LABEL[m]} · {TRANSIT_DAYS[m]} days · {price}"

        mode = st.radio("Shipping method (cheapest first)", list(by_mode), format_func=mode_name,
                        key=f"mode_{key}_{country}_{qty}")
        d = by_mode[mode]
        if d["below_moq"]:
            st.warning(f"{qty:,} units is below the MOQ of {p['moq']:,}. The seller may refuse or "
                       "charge more; the lowest listed tier price is used.")
        st.markdown(receipt(delivered_lines(d, qty), "Total delivered",
                            f"{units(qty)} · {d['mode_label'].lower()}, {d['transit_days']} days",
                            d["total"], d["per_unit"], qty, sym), unsafe_allow_html=True)
        st.markdown(f"<div class='muted'>Price on the original listing: {cny(d['unit_cny'])}/unit "
                    f"≈ {sym}{d['product_per_unit'] or 0:,.2f}</div>", unsafe_allow_html=True)
        for n in d["notes"]:
            st.caption(f"• {n}")
        st.markdown(tag("Estimated", "est") + f"<span class='muted'>{fx_line(S.cur)}. Freight, duty and "
                    "VAT are sample estimates, not a quote: real costs depend on HS code, box size, "
                    "incoterms and the forwarder.</span>", unsafe_allow_html=True)

        can_order = d["total"] is not None
        st.button("🛒 Order · pay 30% deposit", type="primary", key=f"order_{key}", disabled=not can_order,
                  width="stretch", on_click=start_checkout, args=(p, qty, country, mode),
                  help=None if can_order else "Needs a complete delivered price")

    # ---- 3. Supplier trust
    st.markdown(section(3, "Can you trust this seller?"), unsafe_allow_html=True)
    with st.container(border=True):
        # the same score as in the results list (same search, same-platform sales and prices);
        # scored alone for products outside the search
        r = (source == "catalog" and trust_in_search(p, trust_q)) or trust_for(p, d["unit_cny"])
        c1, c2 = st.columns([1, 1.25], gap="large")
        with c1:
            num = (f"<span class='trust-num'>{r['score']}<small>/100</small></span>" if r["score"] is not None
                   else "<span class='trust-num' style='color:#9AA8B6'>n/a</span>")
            st.markdown(f"<div class='trust-head'>{num}{trust_pill(r, big=True)}</div>", unsafe_allow_html=True)
            known = len(r["metrics"]) - len(r["missing"])
            st.markdown(f"<div class='muted'>Based on {known} of {len(r['metrics'])} metrics "
                        f"({r['coverage_pct']}% of the weights)</div>", unsafe_allow_html=True)
            if r["score"] is None:
                st.markdown(f"<div class='muted'>Missing: {esc(', '.join(r['missing']))}</div>",
                            unsafe_allow_html=True)
            for pen in r["penalties"]:
                pts = PENALTY_POINTS.get(pen)
                st.markdown(f"<div class='penalty'>⚠️ {esc(pen)}{f' (−{pts})' if r['score'] is not None and pts else ''}"
                            f"</div>", unsafe_allow_html=True)

            name = s.get("name") or s.get("name_cn")
            cn = (f"<div class='sup-cn'>{esc(s['name_cn'])}</div>"
                  if s.get("name") and s.get("name_cn") and s["name"] != s["name_cn"] else "")
            city = f"<div class='sup-city'>📍 {esc(s['city'])}, China</div>" if s.get("city") else ""
            st.markdown(f"<div class='sup'><div class='sup-name'>{esc(name) or NA}</div>{cn}{city}</div>",
                        unsafe_allow_html=True)
        with c2:
            st.markdown("**Why this score**" + trust_bars(r), unsafe_allow_html=True)
            st.caption("A summary of public signals from the listing and the platform, not an official "
                       "verification.")

        def nice(x):
            return esc((x or "").replace("_", " ").capitalize()) or None

        raw = raw_fields(p)
        scores5 = raw["service_scores_5pt"]
        badges = "".join(f"<span class='chip-b'>{esc(BADGE_EN.get(b, b))}</span>" for b in raw["badges"] or []) or None
        st.markdown("<div class='sub-h'>Seller facts <span>from the listing and the platform</span></div>"
                    + fact_grid([
                        ("Years active", None if raw["years_active"] is None else f"{raw['years_active']:g} years"),
                        ("Store type", esc(STORE_TYPES.get(raw["platform"], {}).get(raw["store_type"], (0, ""))[1])
                         or nice(raw["store_type"])),
                        ("Seller type", nice(raw["seller_type"])),
                        ("Service rating", " / ".join(f"{x:g}" for x in scores5) + " out of 5" if scores5 else None),
                        ("Positive reviews", None if raw["positive_review_pct"] is None else f"{raw['positive_review_pct']:g}%"),
                        ("Repurchase rate", None if raw["repurchase_rate_pct"] is None else f"{raw['repurchase_rate_pct']:g}%"),
                        ({"reviews": "Reviews"}.get(s.get("sales_count_type"), "Sales / orders"),
                         None if raw["sales_count"] is None else f"{raw['sales_count']:,}"),
                        ("Seller credit", nice(raw["taobao_credit_level"])),
                        ("Badges", badges, True),
                    ]), unsafe_allow_html=True)
        st.markdown("**How we score**" + how_we_score_html(), unsafe_allow_html=True)

    # ---- 4. Contact
    st.markdown(section(4, "Contact the supplier"), unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("Chat with the supplier here: you write in English (or your language), they read "
                    "natural business Chinese, and every reply comes back translated and explained.")
        st.button("💬 Contact supplier", type="primary", key=f"contact_{key}",
                  on_click=open_conversation, args=(p, qty, country))
        st.markdown("**Original listing**")
        if p.get("url"):
            site = platform_from_url(p["url"]) or p.get("platform") or "the source site"
            st.link_button(f"Open original listing on {site} ↗", p["url"])
        else:
            st.markdown(f"Original listing link: <span class='na'>{NA}</span>", unsafe_allow_html=True)
            slink = search_link(p)
            if slink:
                st.link_button(f"Search similar items on {p['platform']} ↗", slink)


def page_detail():
    p = get_product(S.pid)
    st.button("← Back to results", on_click=go, args=("results",))
    if not p:
        st.error("Product not found.")
        return
    sample_banner()
    render_detail(p)
