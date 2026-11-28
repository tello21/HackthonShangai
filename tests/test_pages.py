"""Every page renders without errors and shows what it must (AI simulated or off)."""

import re
from unittest import mock

import pytest

from conftest import page_text, run_app
from core import query_translation
from core.catalog import PRODUCTS
from tests.test_ai import PLAN


def test_home_sections(no_ai):
    at = run_app({"view": "home"})
    t = page_text(at)
    assert at.button[0].label == "Search suppliers →"
    for part in ("Search. Compare.", "Trust. Buy.", "From search to checkout",
                 "Trust, explained", "Clear answers.", "Find the product. Know the full picture."):
        assert part in t, part
    # a university project: no hackathon footer, no reference to our database on the home page
    t = re.sub(r"<style>.*?</style>", "", t, flags=re.S)                    # the text, not the stylesheet
    for gone in ("Hackathon", "hackathon", "prototype", "sitefoot", "In our catalog", "catalog", "Rules-based",
                 "In all", "listings →", "demo"):
        assert gone not in t, gone
    assert "Source smarter" not in t and "Yiwugo" not in t and "SourceScan" not in t and "Scoutr" in t
    assert "Link paste" not in t and "Link analyzer" in t
    for p in ("1688", "Taobao", "JD", "Pinduoduo"):
        assert f"<span class='market'>{p}</span>" in t


def test_home_search_starts_empty(no_ai):
    at = run_app({"view": "home", "q": "padel"})       # even when the address still carries a search
    assert at.text_input[0].value == "" and "q" not in at.query_params
    at.text_input[0].input("padel racket")
    at.button[0].click().run()
    assert at.session_state["view"] == "results" and at.session_state["q"] == "padel racket"


def test_trust_explained_changes_with_the_marketplace(no_ai):
    at = run_app({"view": "home"})
    t = page_text(at)
    assert at.session_state["mk_pick"] == "1688" and "Super factory" in t
    at.segmented_control(key="mk_pick").set_value("Pinduoduo").run()
    t = page_text(at)
    assert "Not shown on Pinduoduo" in t and "class='avail" not in t       # general rules, no data tags
    at.segmented_control(key="mk_pick").set_value("JD").run()
    t = page_text(at)
    trust = t[t.index("Trust, explained"):t.index("Clear answers.")]
    assert not any("一" <= ch <= "鿿" for ch in trust)          # no Chinese in the explanation


@pytest.mark.parametrize("tab,view", [("link", "link"), ("messages", "inbox")])
def test_old_addresses(no_ai, tab, view):
    at = run_app({"view": "home", "tab": tab})
    assert at.session_state["view"] == view
    assert run_app({"view": "paste"}).session_state["view"] == "link"      # old Link paste -> Link analyzer


def test_link_analyzer_gives_the_same_page_as_the_search(no_ai):
    at = run_app({"view": "link"})
    assert "Paste a link. Get the full picture." in page_text(at)
    at.text_input(key="la_url").input("https://detail.1688.com/offer/737253173155.html?spm=a26352.13672862")
    at.button(key="la_go").click().run()
    t = page_text(at)
    assert at.session_state["pid"] == "8"
    for part in ("Found:", "Product", "Delivered price", "Total delivered", "Can you trust this seller?",
                 "Why this score", "Seller facts", "How we score", "Contact the supplier"):
        assert part in t, part
    # the same trust score as in the search results (sales and prices compared with the same listings)
    assert "Trust 64 · Good" in t and "Trust 64 · Good" in page_text(run_app({"view": "results", "q": "padel"}))
    # Taobao links are matched by item id, whatever the variant
    at.text_input(key="la_url").input("https://item.taobao.com/item.htm?id=988472666305&skuId=999")
    at.button(key="la_go").click().run()
    assert at.session_state["pid"] == "12"
    # a link outside the catalog says so, without inventing anything
    at.text_input(key="la_url").input("https://item.jd.com/123.html")
    at.button(key="la_go").click().run()
    t = page_text(at)
    assert at.session_state["pid"] is None and "We can't analyse this listing on JD yet" in t
    assert "catalog" not in t and "database" not in t


def test_a_link_in_the_home_search_opens_the_analyzer(no_ai):
    at = run_app({"view": "home"})
    at.text_input[0].input("https://item.jd.com/10238276468659.html")
    at.button[0].click().run()
    assert at.session_state["view"] == "link" and at.session_state["pid"] == "6"
    assert "Total delivered" in page_text(at)


@pytest.mark.parametrize("q,country,cur", [("padel racket", "Italy", "EUR"), ("carbon", "Switzerland", "CHF"),
                                           ("padel", "United States", "USD"), ("racket", "Iceland", "ISK")])
def test_results_grid(no_ai, q, country, cur):
    for qty in ("1", "500", "5000"):
        t = page_text(run_app({"view": "results", "q": q, "qty": qty, "country": country, "cur": cur}))
        assert t.count("<a class='gc'") >= 3 and "Final trust score" in t and "Final price" in t
        if qty != "1":
            assert f"per unit, delivered to {country}" in t
    t = page_text(run_app({"view": "results", "q": "laptop"}))
    assert "No products match" in t
    assert "Chinese query" not in t and "no API key" not in t             # no AI note without a key


def test_italian_query_matches_through_translation():
    with mock.patch.object(query_translation, "plan_search", return_value=(PLAN, None)):
        t = page_text(run_app({"view": "results", "q": "racchetta da padel in carbonio"}))
    assert "Searched as <b>碳纤维板式网球拍</b>" in t and "matched via translation" in t
    assert t.count("<a class='gc'") == 13                    # all 13 rackets


def test_cards_show_photo_demo_label_and_counterfeit_warning(no_ai):
    t = page_text(run_app({"view": "results", "q": "padel", "qty": "500"}))
    assert t.count("class='demo-tag'") == sum(p["demo"] for p in PRODUCTS) == 9
    assert "src='app/static/images/1.jpg'" in t and "src='app/static/images/13.png'" in t
    assert t.count("⚠ Possible counterfeit") == 1
    assert "Trust 25 · High risk" in t and "Trust 48 · Caution" in t
    # the product page shows the same score as the list (same search context), even after a reload
    detail = page_text(run_app({"view": "detail", "pid": "2", "q": "padel", "qty": "500"}))
    assert "Possible counterfeit brand" in detail and "(−30)" in detail and "demo data" in detail
    assert "Trust 25 · High risk" in detail
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


def test_compare_page(no_ai):
    assert "Compare. Verify. Choose." in page_text(run_app({"view": "compare", "cmp": "1,2,3"}))
