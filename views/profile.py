"""Profile: the buyer's orders and profile settings (name, company, email and the
defaults used for every search: delivery country, currency, quantity)."""

import streamlit as st

from components.state import S
from components.ui import currency_label, esc
from core import profile as P
from core.pricing import COUNTRIES, CURRENCIES
from views.checkout import render_orders_list


def _settings_form():
    p = S.profile
    with st.form("profile_form", border=True):
        st.markdown("**About you**")
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", value=p["name"], placeholder="Your name")
        company = c2.text_input("Company", value=p["company"], placeholder="Optional")
        email = st.text_input("Email", value=p["email"], placeholder="you@company.com",
                              help="Kept on this computer only: nothing is sent anywhere.")
        st.markdown("**Search defaults** — used every time you open the site")
        c3, c4, c5 = st.columns([1.4, 1, 0.9])
        countries, currencies = list(COUNTRIES), list(CURRENCIES)
        country = c3.selectbox("Deliver to", countries,
                               index=countries.index(p["country"]) if p["country"] in countries else 0)
        currency = c4.selectbox("Currency", currencies, format_func=currency_label,
                                index=currencies.index(p["currency"]) if p["currency"] in currencies else 0)
        quantity = c5.number_input("Quantity", min_value=1, step=50, value=int(p["quantity"] or 500))
        saved = st.form_submit_button("Save profile", type="primary")
    if saved:
        new = dict(name=name.strip(), company=company.strip(), email=email.strip(),
                   country=country, currency=currency, quantity=int(quantity))
        errors = P.validate(new)
        if errors:
            for e in errors:
                st.error(e)
            return
        S.profile = P.save_profile(new)
        S.country, S.cur, S.qty = country, currency, int(quantity)   # the new defaults apply now
        st.success("Profile saved. Your search defaults are updated.")


def page_profile():
    p = S.profile
    who = esc(p["name"]) or "Your profile"
    sub = " · ".join(esc(x) for x in (p["company"], p["email"]) if x) or "Add your details below"
    st.markdown(f"<div class='profile-head'><span class='avatar big'>{esc(P.initials(p))}</span>"
                f"<div><div class='pn'>{who}</div><div class='pc2'>{sub}</div></div></div>",
                unsafe_allow_html=True)

    st.markdown(f"<div class='section-h'>Your orders ({len(S.orders)})</div>", unsafe_allow_html=True)
    render_orders_list()

    st.markdown("<div class='section-h'>Profile settings</div>", unsafe_allow_html=True)
    _settings_form()
