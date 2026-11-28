"""Checkout and orders with a SIMULATED payment: no real money moves and no card data
is asked for. 30% deposit to the supplier, 70% balance before shipping; shipping,
duty, VAT and customs are paid on arrival."""

import time

import streamlit as st

from components.state import S, go, link
from components.ui import NA, cny, esc, fx_line, money, pagehero, platform_tag, receipt, tag, units
from core import orders as O
from core.catalog import get_product
from core.pricing import SYMBOL, delivered
from views.product import delivered_lines

SIM_NOTE = ("Simulated payment: no money moves and no card details are needed. "
            "Never enter real card data on this site.")


def _priced_card(card, unit_price_cny):
    """The product card with the negotiated unit price replacing the listed tiers."""
    if unit_price_cny is None:
        return card
    return dict(card, tiers=[[1, unit_price_cny]])


def _place_order(card, qty, country, d, unit_price_cny, negotiated, conv_id):
    order = O.new_order(card, qty, country, S.cur, d, unit_price_cny, negotiated, conv_id)
    O.pay_deposit(order)
    S.orders[order["id"]] = order
    O.save_orders(S.orders)
    S.checkout = None
    go("orders", order=order["id"])


def page_checkout():
    co = S.get("checkout")
    if not co:
        st.info("Start an order from a product page (“Order · pay 30% deposit”).")
        return
    card, qty, country = co["card"], co["qty"], co["country"]
    negotiated = co.get("unit_price_cny") is not None
    priced = _priced_card(card, co.get("unit_price_cny"))
    d = delivered(priced, qty, country, S.cur, co.get("mode") or "auto")
    sym = SYMBOL[S.cur]

    st.markdown(pagehero("03 / Checkout", "Review. Confirm. Buy.", "Review the product, the seller and the "
                         "delivered cost before placing the order.", steps=2), unsafe_allow_html=True)
    st.markdown(f"{platform_tag(card.get('platform'))} **{esc(card.get('title_en') or NA)}**<br>"
                f"<span class='muted'>{esc((card.get('supplier') or {}).get('name') or NA)} · "
                f"{units(qty)} to {esc(country)}</span>", unsafe_allow_html=True)
    if negotiated:
        st.markdown(tag(f"Negotiated price {cny(co['unit_price_cny'])}/unit", "ok"), unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**Delivered price**")
        st.markdown(receipt(delivered_lines(d, qty), "Total delivered",
                            f"{d['mode_label']}, {d['transit_days']} days", d["total"], d["per_unit"], qty, sym),
                    unsafe_allow_html=True)
        st.caption(fx_line(S.cur))

    if d["total"] is None:
        st.warning("The delivered price is not complete (e.g. weight or duty rate not available), "
                   "so this order can't be placed yet.")
        return

    deposit = d["product"] * O.DEPOSIT_PCT / 100
    with st.container(border=True):
        st.markdown("**When you pay**")
        st.markdown(receipt([
            (f"Now · deposit {O.DEPOSIT_PCT}% to the supplier", deposit, "production starts after the deposit"),
            (f"Before shipping · balance {100 - O.DEPOSIT_PCT}%", d["product"] - deposit,
             "when the supplier finishes production"),
            ("On arrival · shipping, duty, VAT, customs", d["total"] - d["product"],
             "paid to the forwarder and customs"),
        ], "Total", "estimated", d["total"], d["per_unit"], qty, sym), unsafe_allow_html=True)

    st.markdown(tag("Simulated payment", "sample") + f"<span class='muted'>{SIM_NOTE}</span>",
                unsafe_allow_html=True)
    st.button(f"Pay deposit {money(deposit, sym)} (simulated)", type="primary", width="stretch",
              key="pay_deposit", on_click=_place_order,
              args=(card, qty, country, d, co.get("unit_price_cny"), negotiated, co.get("conv")))
    if get_product(card.get("id")):
        st.button("Cancel", on_click=go, args=("detail",), kwargs={"pid": card["id"]}, key="cancel_checkout")
    else:
        st.button("Cancel", on_click=go, args=("home",), kwargs={"tab": "search"}, key="cancel_checkout")


# ---------------------------------------------------------------------------- orders
def _act(order_id, fn):
    fn(S.orders[order_id])
    O.save_orders(S.orders)


def order_timeline(order):
    reached = {s for s, _ in order["history"]}
    when = {s: t for s, t in order["history"]}
    items = []
    for i, (status, label) in enumerate(O.STEPS):
        cls = "now" if status == order["status"] else ("done" if status in reached else "todo")
        t = f"<span class='t'>{time.strftime('%d %b %H:%M', time.localtime(when[status]))}</span>" \
            if status in when else ""
        items.append(f"<li class='{cls}'>{label}{t}</li>")
    return "<ul class='tl'>" + "".join(items) + "</ul>"


def page_order(order):
    sym = SYMBOL[order["currency"]]
    st.markdown(f"<a class='rh-back' href='{link(view='profile', order=None)}' target='_self'>← Your orders</a>",
                unsafe_allow_html=True)
    st.markdown(pagehero("Your order", f"Order {esc(order['id'])}"), unsafe_allow_html=True)
    st.markdown(f"{platform_tag(order['platform'])} **{esc(order['product'] or NA)}**<br>"
                f"<span class='muted'>{esc(order['supplier'] or NA)} · {units(order['qty'])} to "
                f"{esc(order['country'])} · {esc(order['mode_label'])}, {order['transit_days']} days</span>",
                unsafe_allow_html=True)
    if order.get("negotiated"):
        st.markdown(tag(f"Negotiated price {cny(order['unit_price_cny'])}/unit", "ok"), unsafe_allow_html=True)

    st.markdown(order_timeline(order), unsafe_allow_html=True)

    oid = order["id"]
    if order["status"] == "deposit_paid":
        lead = f" (about {order['lead_days']} days)" if order.get("lead_days") else ""
        st.caption(f"The supplier is producing your order{lead}.")
        st.button("Simulate: supplier finishes production", key=f"prod_{oid}", on_click=_act,
                  args=(oid, O.finish_production))
    elif order["status"] == "production_done":
        st.button(f"Pay balance {money(order['balance'], sym)} (simulated)", type="primary", key=f"bal_{oid}",
                  on_click=_act, args=(oid, O.pay_balance), width="stretch")
    elif order["status"] == "balance_paid":
        st.button("Simulate: supplier ships the goods", key=f"ship_{oid}", on_click=_act, args=(oid, O.ship))
    elif order["status"] == "shipped":
        st.success(f"Shipped by {order['mode_label'].lower()}: expected in {order['transit_days']} days. "
                   f"Shipping, duty, VAT and customs ({money(order['on_arrival'], sym)}) are paid on arrival.")

    with st.container(border=True):
        st.markdown("**Payments**")
        rows = [(f"{p['what']} · ref {p['ref']}", p["amount"],
                 time.strftime("%d %b %H:%M", time.localtime(p["ts"]))) for p in order["payments"]]
        st.markdown(receipt(rows or [("No payments yet", None, "")], "Paid so far", "simulated",
                            O.paid_total(order), O.paid_total(order) / order["qty"], order["qty"], sym),
                    unsafe_allow_html=True)
        st.caption(f"Order total {money(order['total'], sym)} delivered · {SIM_NOTE}")
    if order.get("conv"):
        st.markdown(f"<a href='{link(view='chat', conv=order['conv'])}' target='_self'>💬 Open the chat with "
                    f"the supplier</a>", unsafe_allow_html=True)


def page_orders():
    """One order (app.py sends the address without an order to the profile)."""
    page_order(S.orders[S.order])


def render_orders_list():
    if not S.orders:
        st.info("No orders yet. Open a product and tap “Order · pay 30% deposit”.")
        return
    rows = []
    for o in sorted(S.orders.values(), key=lambda o: o["created"], reverse=True):
        label = O.STATUS_LABEL[o["status"]]
        rows.append(f"<a class='oc' href='{link(view='orders', order=o['id'])}' target='_self'>"
                    f"<span class='ib-top'><span class='ib-name'>{esc(o['product'] or NA)}</span>"
                    f"<span class='ib-time'>{o['id']}</span></span>"
                    f"<span class='ib-prod'>{platform_tag(o['platform'])} {units(o['qty'])} · "
                    f"{money(o['total'], SYMBOL[o['currency']])} delivered</span>"
                    f"<span class='ib-last'>{label}</span></a>")
    st.markdown("".join(rows), unsafe_allow_html=True)
