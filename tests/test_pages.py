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


@pytest.mark.parametrize("q,country,cur", [("tote bag", "Italy", "EUR"), ("water bottle", "Switzerland", "CHF"),
                                           ("mug", "United States", "USD"), ("led strip", "Iceland", "ISK")])
def test_results_list(no_ai, q, country, cur):
    for qty in ("1", "500", "5000"):
        t = page_text(run_app({"view": "results", "q": q, "qty": qty, "country": country, "cur": cur}))
        assert t.count("class='pc") >= 3 and "Trust " in t
        if qty != "1":   # at 1 unit most items are below MOQ -> honestly 'not available'
            assert "Best price" in t and "/unit delivered" in t
    t = page_text(run_app({"view": "results", "q": "laptop"}))


def test_italian_query_matches_through_translation():
    with mock.patch.object(query_translation, "plan_search", return_value=(PLAN, None)):
        t = page_text(run_app({"view": "results", "q": "borsa di tela con logo"}))
    assert "Searched as <b>帆布袋定制logo</b>" in t and "matched via translation" in t
    assert t.count("class='mk'") == 4                       # the four tote bags


def test_every_product_page(no_ai):
    for p in PRODUCTS:
        at = run_app({"view": "detail", "pid": p["id"], "qty": "500"})
        t = page_text(at)
        assert "Total delivered" in t and ("ECB" in t or "sample rate" in t), p["id"]
        assert at.radio[0].label.startswith("Shipping method")
        if p["weight_kg"] is None:
            assert "needs weight" in t and at.button(key=f"order_{p['id']}").disabled


def test_switching_shipping_mode_updates_the_receipt(no_ai):
    at = run_app({"view": "detail", "pid": "WB-01", "qty": "1"})
    assert at.radio[0].options[0].startswith("Express courier")
    at.radio[0].set_value("sea").run()
    assert "Shipping · Sea freight" in page_text(at)


def test_compare_and_old_paste_address(no_ai):
    run_app({"view": "compare", "cmp": "TB-01,TB-02,WB-01"})
    at = run_app({"view": "paste"})                         # old link still lands on Link paste
    assert at.session_state["view"] == "home" and at.session_state["tab"] == "link"
