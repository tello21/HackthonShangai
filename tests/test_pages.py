"""Every page renders without errors and shows what it must (AI simulated or off)."""

from unittest import mock

import pytest

from conftest import page_text, run_app
from core import query_translation
from core.catalog import PRODUCTS
from tests.test_ai import PLAN


@pytest.mark.parametrize("tab,expected", [
    ("search", "Find trusted suppliers in China"), ("link", "Paste a link"), ("messages", "Your suppliers")])
def test_home_three_way_bar(no_ai, tab, expected):
    at = run_app({"view": "home", "tab": tab})
    assert expected in page_text(at)
    assert at.session_state["home_tab"] == tab


@pytest.mark.parametrize("q,country,cur", [("padel racket", "Italy", "EUR"), ("carbon", "Switzerland", "CHF"),
                                           ("padel", "United States", "USD"), ("racket", "Iceland", "ISK")])
def test_results_list(no_ai, q, country, cur):
    for qty in ("1", "500", "5000"):
        t = page_text(run_app({"view": "results", "q": q, "qty": qty, "country": country, "cur": cur}))
        assert t.count("class='pc") >= 3 and "Trust " in t
        if qty != "1":   # at 1 unit most items are below MOQ -> honestly 'not available'
            assert "Best price" in t and "/unit delivered" in t
    t = page_text(run_app({"view": "results", "q": "laptop"}))


def test_italian_query_matches_through_translation():
    with mock.patch.object(query_translation, "plan_search", return_value=(PLAN, None)):
        t = page_text(run_app({"view": "results", "q": "racchetta da padel in carbonio"}))
    assert "Searched as <b>碳纤维板式网球拍</b>" in t and "matched via translation" in t
    assert t.count("class='mk'") == 13                      # all 13 rackets


def test_cards_show_photo_demo_label_and_counterfeit_warning(no_ai):
    t = page_text(run_app({"view": "results", "q": "padel", "qty": "500"}))
    assert t.count("class='demo-tag'") == sum(p["demo"] for p in PRODUCTS) == 9
    assert "src='app/static/images/1.jpg'" in t and "src='app/static/images/13.png'" in t
    assert "<span class='warn'>⚠ Possible counterfeit brand" in t
    assert "Trust 24 · High risk" in t and "Trust 48 · Caution" in t
    # the product page shows the same score as the list (same search context), even after a reload
    detail = page_text(run_app({"view": "detail", "pid": "2", "q": "padel", "qty": "500"}))
    assert "Possible counterfeit brand" in detail and "(−30)" in detail and "demo data" in detail
    assert "Trust 24 · High risk" in detail
    jd = page_text(run_app({"view": "detail", "pid": "6", "q": "padel", "qty": "500"}))
    assert "Trust 48 · Caution" in jd and "Price much lower than similar listings" in jd


def test_every_product_page(no_ai):
    for p in PRODUCTS:
        at = run_app({"view": "detail", "pid": p["id"], "qty": "500"})
        t = page_text(at)
        assert "Total delivered" in t and ("ECB" in t or "sample rate" in t), p["id"]
        assert at.radio[0].label.startswith("Shipping method")
        if p["weight_kg"] is None:
            assert "needs weight" in t and at.button(key=f"order_{p['id']}").disabled


def test_switching_shipping_mode_updates_the_receipt(no_ai):
    at = run_app({"view": "detail", "pid": "3", "qty": "1"})
    assert at.radio[0].options[0].startswith("Express courier")
    at.radio[0].set_value("sea").run()
    assert "Shipping · Sea freight" in page_text(at)


def test_compare_and_old_paste_address(no_ai):
    run_app({"view": "compare", "cmp": "1,2,3"})
    at = run_app({"view": "paste"})                         # old link still lands on Link paste
    assert at.session_state["view"] == "home" and at.session_state["tab"] == "link"
