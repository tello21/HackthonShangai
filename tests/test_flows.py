"""User flows end to end: messages with the supplier, link paste, order + simulated payment."""

import json
from unittest import mock

from conftest import page_text, run_app
from core import ai, messages as M
from core import orders as O
from tests.test_ai import AI_LISTING

REPLY = "亲，500个的话单价¥17.5，起订量50个，交期15天左右。付款是30%定金，发货前付70%尾款。需要印logo吗？"


def fake_ask(system, messages, schema=None, effort="low", max_tokens=8000):
    if schema is M.OUT_SCHEMA:
        return {"zh": "您好，请问500件的最优单价是多少？交期多久？",
                "back_en": "Hello, what is your best unit price for 500 pieces? What is the lead time?"}, None
    if schema is M.IN_SCHEMA:
        return {"en": "Dear, for 500 pcs the unit price is ¥17.5, MOQ 50, lead time about 15 days. "
                      "Payment: 30% deposit, 70% before shipping. Do you need a logo printed?",
                "meaning": "A standard first quote with some room to negotiate.",
                "highlights": ["单价¥17.5", "起订量50个", "交期15天左右", "30%定金"],
                "terms": {"unit_price_cny": 17.5, "price_for_quantity": 500, "moq_units": 50,
                          "lead_time": "about 15 days", "payment_terms": "30% deposit, 70% before shipping",
                          "sample_cost": "", "shipping_terms": "", "customization": "",
                          "seller_type": "", "certifications": ""},
                "suggestions": ["Can you do ¥16 for 500 units?", "Yes, one-colour logo. Extra cost?"]}, None
    assert "底价" in system and "T800" in system      # persona built from the product card
    return REPLY, None


def button(at, label):
    return next(b for b in at.button if b.label == label)


def test_chat_with_translator_both_ways_and_order_at_negotiated_price(no_ai):
    with mock.patch.object(M, "ask", side_effect=fake_ask):
        at = run_app({"view": "detail", "pid": "1", "qty": "500", "country": "Italy", "cur": "EUR"})
        at.button(key="contact_1").click().run()
        cid = at.session_state["conv"]
        assert at.session_state["view"] == "chat"
        assert "best price for 500 units" in at.text_area(key=f"draft_{cid}").value
        assert at.button(key=f"send_{cid}").disabled                   # preview first

        at.button(key=f"pv_{cid}").click().run()                       # outgoing translation
        t = page_text(at)
        assert "您好，请问500件" in t and "Means: Hello, what is your best unit price" in t

        at.button(key=f"send_{cid}").click().run()                     # supplier replies, incoming analysis
        t = page_text(at)
        assert "<mark>单价¥17.5</mark>" in t and "What they mean:" in t and "Lead time: about 15 days" in t
        assert "¥17.5 @ 500 pcs<span class='src'>from chat</span>" in t

        at.button(key=f"recalc_{cid}").click().run()
        r = at.session_state["convs"][cid]["recalc"]
        assert r["after"] < r["before"]

        button(at, "Can you do ¥16 for 500 units?").click().run()     # suggested reply -> draft
        assert at.text_area(key=f"draft_{cid}").value == "Can you do ¥16 for 500 units?"

        at.button(key=f"order_neg_{cid}").click().run()                # order at the negotiated price
        assert at.session_state["view"] == "checkout"
        assert "Negotiated price ¥17.50/unit" in page_text(at)

    stored = json.load(open(M.STORE, encoding="utf-8"))
    assert len(stored[cid]["messages"]) == 2
    inbox = page_text(run_app({"view": "home", "tab": "messages"}))   # survives a reload
    assert "Shenzhen Hengtai Carbon Fiber" in inbox


def test_chat_without_api_key_says_why(no_ai):
    at = run_app({"view": "detail", "pid": "3", "qty": "500"})
    at.button(key="contact_3").click().run()
    cid = at.session_state["conv"]
    at.button(key=f"pv_{cid}").click().run()
    assert any("Translation not available — no API key configured" in w.value for w in at.warning)
    assert at.button(key=f"send_{cid}").disabled


# ---------------------------------------------------------------- link paste
def paste(at, url="", text=""):
    if url:
        at.text_input(key="lp_url").input(url)
    if text:
        at.text_area(key="lp_text").input(text)
    button(at, "Analyze").click().run()
    return page_text(at)


def test_link_paste_known_link_gives_full_analysis(no_ai):
    at = run_app({"view": "home", "tab": "link"})
    t = paste(at, url="https://detail.1688.com/offer/1037995681915.html?spm=a2615")
    assert "Found in our catalog" in t and "Total delivered" in t


def test_link_paste_unknown_link_asks_for_screenshot_or_text(no_ai):
    at = run_app({"view": "home", "tab": "link"})
    t = paste(at, url="https://item.taobao.com/item.htm?id=612345")
    assert "Got the link on Taobao" in t and "screenshot" in t


def test_link_paste_text_read_by_ai(no_ai):
    with mock.patch.object(ai, "ask", return_value=(AI_LISTING, None)):
        at = run_app({"view": "home", "tab": "link"})
        t = paste(at, url="https://detail.1688.com/offer/612345.html", text="12安帆布手提袋 …")
    assert "Listing read from your text" in t and "12 oz canvas tote bag" in t and "Total delivered" in t


def test_link_paste_falls_back_to_rules_without_ai(no_ai):
    at = run_app({"view": "home", "tab": "link"})
    button(at, "Use an example listing").click().run()
    t = paste(at)
    assert "AI reading not available (no API key configured)" in t and "Total delivered" in t


# ---------------------------------------------------------------- order + simulated payment
def test_order_with_simulated_payment(no_ai):
    at = run_app({"view": "detail", "pid": "1", "qty": "500", "country": "Italy", "cur": "EUR"})
    at.button(key="order_1").click().run()
    t = page_text(at)
    assert at.session_state["view"] == "checkout"
    assert "Now · deposit 30% to the supplier" in t and "On arrival" in t and "no card details" in t
    at.button(key="pay_deposit").click().run()
    oid = at.session_state["order"]
    assert at.session_state["view"] == "orders"
    order = at.session_state["orders"][oid]
    assert order["status"] == "deposit_paid" and order["payments"][0]["ref"].startswith("SIM-")

    at.button(key=f"prod_{oid}").click().run()
    at.button(key=f"bal_{oid}").click().run()
    at.button(key=f"ship_{oid}").click().run()
    assert at.session_state["orders"][oid]["status"] == "shipped"
    assert "Shipped by" in " ".join(s.value for s in at.success)
    stored = json.load(open(O.STORE, encoding="utf-8"))
    assert stored[oid]["status"] == "shipped" and len(stored[oid]["payments"]) == 2
