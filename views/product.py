"""Product page: product card, delivered price, supplier, contact + order.
Also used to show the result of Link paste."""

import pandas as pd
import streamlit as st

from components.state import S, go
from components.ui import (NA, cny, esc, fx_line, image_html, kv_table, receipt, sample_banner, score_pill,
                           search_link, tag, units, val)
from core import messages as M
from core.pricing import COUNTRIES, DUTY, MODE_LABEL, SYMBOL, TRANSIT_DAYS, compare_modes, delivered, fx_rate
from core.supplier_score import supplier_score
from views.live import find_product, set_buyer_details


def open_conversation(p, qty, country):
    """Contact supplier: open the existing chat for this product, or start one with the
    product, quantity, country and delivered price loaded as context."""
    existing = next((c for c in S.convs.values()
                     if c["pid"] == p["id"] and c.get("product") == p.get("title_en")), None)
    if existing:
        conv = existing
    else:
        d = delivered(p, qty, country, S.cur)
        conv = M.new_conversation(p, qty, country, S.cur, d["per_unit"])
        conv["card"] = dict(p)  # product card snapshot (pasted listings too)
        S.convs[conv["id"]] = conv
        M.save_conversations(S.convs)
        S[f"draft_{conv['id']}"] = M.quick_action_text("Ask for quote", qty, country, p.get("moq"))
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


def _save_buyer_details(pid):
    w = S.get(f"lw_{pid}") or 0
    c = S.get(f"lc_{pid}")
    set_buyer_details(pid, w / 1000 if w > 0 else None, None if c in (None, "(not set)") else c)


def buyer_details_box(p):
    """Live listings have no weight: let the buyer add it (and fix the category) to get the
    delivered price. Values are marked user-provided and reused in the results list."""
    pid = p["id"]
    if not p.get("weight_user") and p.get("weight_kg") is None:
        st.markdown("**This listing has no weight.** Add the weight per unit (ask the supplier, or use a "
                    "similar product) to see the delivered price.")
    c1, c2 = st.columns(2)
    c1.number_input("Weight per unit (g)", min_value=0, step=10, key=f"lw_{pid}",
                    value=int((p.get("weight_kg") or 0) * 1000), on_change=_save_buyer_details, args=(pid,))
    cats = ["(not set)"] + list(DUTY)
    c2.selectbox("Product category (for the duty rate)", cats, key=f"lc_{pid}",
                 index=cats.index(p["category"]) if p.get("category") in cats else 0,
                 on_change=_save_buyer_details, args=(pid,))
    if p.get("category_guessed"):
        st.caption(f"Category guessed from the title: {p['category']}. Change it if it's wrong.")


def render_detail(p, source="catalog"):
    key = p["id"]
    s = p.get("supplier") or {}

    # ---- 1. Product page
    st.subheader("1 · Product")
    with st.container(border=True):
        c_img, c_info = st.columns([1, 2])
        with c_img:
            st.markdown(image_html(p, 260), unsafe_allow_html=True)
            if p.get("live"):
                st.markdown(tag("Live Yiwugo listing", "ok"), unsafe_allow_html=True)
            elif source != "catalog":
                st.markdown(tag(f"Read from your {source}", "est"), unsafe_allow_html=True)
        with c_info:
            st.markdown(f"### {esc(p.get('title_en') or p.get('title_cn') or NA)}")
            if p.get("live") and not p.get("title_en"):
                st.markdown(tag("English name not available", "na"), unsafe_allow_html=True)
            elif p.get("title_en_source") == "ai":
                st.markdown(tag("English name translated by AI", "est"), unsafe_allow_html=True)
            elif p.get("title_en_source") == "glossary" or (source != "catalog" and not p.get("live")
                                                              and p.get("title_en")):
                st.markdown(tag("Translated title — approximate", "est"), unsafe_allow_html=True)
            if p.get("title_cn") and p.get("title_en"):
                st.markdown(f"<span class='muted'>Original title: {esc(p['title_cn'])}</span>",
                            unsafe_allow_html=True)
            moq = units(p["moq"]) if p.get("moq") is not None else None
            weight = f"{p['weight_kg']*1000:,.0f} g" if p.get("weight_kg") is not None else None
            if weight and p.get("weight_user"):
                weight += " " + tag("user-provided", "est")
            prod = f"{p['production_days']} days" if p.get("production_days") is not None else None
            st.markdown(kv_table([
                ("Platform", val(esc(p.get("platform")) or None)),
                ("Material", val(esc(p.get("material")) or None)),
                ("Size", val(esc(p.get("size")) or None)),
                ("Weight (per unit)", val(weight)),
                ("MOQ", val(moq)),
                ("Production time", val(prod)),
                ("Customisation", val(esc(p.get("customisation")) or None)),
            ]), unsafe_allow_html=True)

        st.markdown("**Price tiers** (as listed by the seller)")
        if p.get("tiers"):
            fx, sym = fx_rate(S.cur), SYMBOL[S.cur]
            tiers = sorted(p["tiers"])
            rows = []
            for i, (mq, price) in enumerate(tiers):
                rng = f"{mq:,} – {tiers[i+1][0]-1:,}" if i + 1 < len(tiers) else f"{mq:,}+"
                row = {"Quantity": rng, "Price (CNY)": f"¥{price:,.2f}"}
                if S.cur != "CNY":
                    row[f"≈ {S.cur}"] = f"{sym}{price*fx:,.2f}"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="content")
            st.caption(fx_line(S.cur))
        else:
            st.markdown(f"<span class='na'>{NA}</span>", unsafe_allow_html=True)

    # ---- 2. Delivered price
    st.subheader("2 · Delivered price")
    with st.container(border=True):
        if p.get("live"):
            buyer_details_box(p)
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
    st.subheader("3 · Can you trust this seller?")
    with st.container(border=True):
        score, reasons = supplier_score(s)
        c1, c2 = st.columns([1.2, 1])
        with c1:
            name = s.get("name") or s.get("name_cn")
            st.markdown(f"#### {esc(name) or NA}")
            if s.get("name") and s.get("name_cn"):
                st.markdown(f"<span class='muted'>{esc(s['name_cn'])}</span>", unsafe_allow_html=True)
            years = f"{s['years']} years" if s.get("years") is not None else None
            badges = " ".join(tag(esc(b), "est") for b in s.get("badges") or []) or None
            st.markdown(kv_table([
                ("City", val(esc(s.get("city")) or None)),
                ("Type", val((s.get("type") or "").capitalize() or None)),
                ("Years active", val(years)),
                ("Badges", val(badges)),
                ("Response rate", val(None if s.get("response_rate") is None else f"{s['response_rate']:.0f}%")),
                ("Repeat buyers", val(None if s.get("repeat_buyer_rate") is None else f"{s['repeat_buyer_rate']:.0f}%")),
            ]), unsafe_allow_html=True)
        with c2:
            st.markdown(f"**Trust score**<br>{score_pill(score)}", unsafe_allow_html=True)
            st.caption("Starts at 50 and moves with each fact we know about the seller — every reason is "
                       "listed below. Sample rules for now.")
            for text, pts in reasons:
                if pts > 0:
                    st.markdown(f"✅ {text} (**+{pts}**)")
                elif pts < 0:
                    st.markdown(f"⚠️ {text} (**{pts}**)")
                else:
                    st.markdown(f"<span class='muted'>• {text}</span>", unsafe_allow_html=True)

    # ---- 4. Contact
    st.subheader("4 · Contact the supplier")
    with st.container(border=True):
        st.markdown("Chat with the supplier here: you write in English (or your language), they read "
                    "natural business Chinese, and every reply comes back translated and explained.")
        st.button("💬 Contact supplier", type="primary", key=f"contact_{key}",
                  on_click=open_conversation, args=(p, qty, country))
        st.markdown("**Original listing**")
        if p.get("url"):
            st.link_button(f"Open original listing on {p.get('platform') or 'source site'} ↗", p["url"])
        else:
            st.markdown(f"Original listing link: <span class='na'>{NA}</span>", unsafe_allow_html=True)
            slink = search_link(p)
            if slink:
                st.link_button(f"Search similar items on {p['platform']} ↗", slink)


def page_detail():
    p = find_product(S.pid)
    st.button("← Back to results", on_click=go, args=("results",))
    if not p:
        st.error("Product not found.")
        return
    if not p.get("live"):
        sample_banner()
    render_detail(p, "catalog" if not p.get("live") else "live")
