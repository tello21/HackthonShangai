"""Profile (orders + settings) and the 'How Scoutr works' section."""

import json

from conftest import page_text, run_app
from core import profile as P


def by_label(widgets, label):
    return next(w for w in widgets if w.label == label)


def test_empty_profile(no_ai):
    t = page_text(run_app({"view": "profile"}))
    assert "Your profile" in t and "Your orders (0)" in t and "No orders yet" in t
    assert "Profile settings" in t


def test_save_settings_and_defaults_apply(no_ai):
    at = run_app({"view": "profile"})
    by_label(at.text_input, "Name").input("Giulia Rossi")
    by_label(at.text_input, "Company").input("Rossi Srl")
    by_label(at.text_input, "Email").input("giulia@rossi.example")
    by_label(at.selectbox, "Deliver to").set_value("Germany")
    by_label(at.number_input, "Quantity").set_value(2000)
    by_label(at.button, "Save profile").click().run()
    assert not at.exception, at.exception
    assert "Profile saved" in page_text(at)
    stored = json.load(open(P.STORE, encoding="utf-8"))
    assert stored["name"] == "Giulia Rossi" and stored["country"] == "Germany" and stored["quantity"] == 2000

    home = run_app({"view": "home"})                       # a new visit uses the saved defaults
    assert home.session_state["country"] == "Germany" and home.session_state["qty"] == 2000
    assert "<span class='avatar'>GR</span>Profile" in page_text(home)
    # an address that says otherwise still wins
    assert run_app({"view": "home", "country": "Spain"}).session_state["country"] == "Spain"


def test_bad_email_is_refused(no_ai):
    at = run_app({"view": "profile"})
    by_label(at.text_input, "Email").input("not-an-email")
    by_label(at.button, "Save profile").click().run()
    assert any("email address" in e.value for e in at.error)
    assert not P.load_profile()["email"]


def test_orders_appear_in_the_profile(no_ai):
    at = run_app({"view": "detail", "pid": "1", "qty": "500"})
    at.button(key="order_1").click().run()
    at.button(key="pay_deposit").click().run()
    t = page_text(run_app({"view": "orders"}))             # no order given -> the profile with the list
    assert "Your orders (1)" in t and "T800 carbon fiber" in t
    assert "Deposit paid" in t


def test_how_it_works_section_on_home(no_ai):
    t = page_text(run_app({"view": "home"}))
    assert "Clear answers." in t and "id='faq'" in t
    for q in ("How does the search work?", "How do you calculate supplier trust?",
              "What is included in the delivered price?", "Does a high trust score guarantee a supplier is safe?",
              "Missing data is not hidden", "Red flags cost points"):
        assert q in t, q
    detail = page_text(run_app({"view": "detail", "pid": "1"}))      # "How we score" on every product page
    for q in ("What happens when data is missing?", "What is the price red flag?",
              "What if the brand looks counterfeit?", "Is the trust score an official verification?"):
        assert q in detail, q
