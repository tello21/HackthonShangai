"""Live Yiwugo listings (PR #1). Yiwugo prices are fen on the wire and yuan on the page.
Missing facts stay empty. No test calls yiwugo.com: search results are simulated."""

from unittest import mock

import json

from conftest import page_text, run_app
from core import query_translation, yiwugo
from core.yiwugo import listing_from_api, yuan_from_fen
from core.yiwugo import search as real_search          # conftest stubs yiwugo.search in every test
from core.yiwugo import with_details

ITEM = {"id": 940179442, "title": "帆布手提袋", "sellPrice": 430, "startNum": 1000,
        "shopName": "义乌市天汇制袋厂", "picture1": "http://img.example/bag.jpg", "isAd": "0"}
DETAIL = {"years": 5, "detail": {"productExtendList": [{"name": "材质", "value": "帆布"},
                                                       {"name": "尺寸", "value": "按要求定制"}],
                                 "sdiProductsPriceList": [{"startNumber": 1000, "conferPrice": 430}]}}


def live_listing():
    return listing_from_api(ITEM, DETAIL)


# ---------------------------------------------------------------- network logic (Yiwugo simulated)
class FakeYiwugo:
    """Answers like yiwugo.com and counts the requests."""

    def __init__(self, expire_first_api_call=False):
        self.calls = {"page": 0, "search": 0, "detail": 0}
        self.expire = expire_first_api_call
        self.token = 0

    def get(self, url, headers=None, opener=None, timeout=8):
        if "/search?q=" in url:
            self.calls["page"] += 1
            self.token += 1
            return f'<script>{{"csrf":"tok{self.token}"}}</script>'
        if "/api/search/" in url:
            self.calls["search"] += 1
            if self.expire and self.calls["search"] == 1:
                return "<html>session expired</html>"
            row = dict(ITEM, marketOrAdress="义乌国际商贸城四区")
            return json.dumps({"content": {"prslist": [dict(row, isAd="1", id=7), row]}})
        if "/api/product/detail.htm" in url:
            self.calls["detail"] += 1
            return json.dumps({"content": DETAIL})
        raise AssertionError(url)


def fresh_module(monkeypatch, fake):
    monkeypatch.setattr(yiwugo, "_get", fake.get)
    monkeypatch.setattr(yiwugo, "_token", None)
    monkeypatch.setattr(yiwugo, "_details", {})


def test_token_reused_and_details_not_awaited(monkeypatch):
    fake = FakeYiwugo()
    fresh_module(monkeypatch, fake)
    first = real_search("帆布袋")
    real_search("保温杯")
    assert fake.calls == {"page": 1, "search": 2, "detail": 0}   # one token for both searches
    assert len(first) == 1                                        # the ad row is skipped
    p = first[0]
    assert p["details_loaded"] is False and p["supplier"]["city"] == "Yiwu"
    assert p["tiers"] == [(1000, 4.3)] and p["material"] is None  # from the search row only

    full = with_details(p)                                         # product page: details now
    assert fake.calls["detail"] == 1
    assert full["details_loaded"] is True and full["material"] == "帆布" and full["supplier"]["years"] == 5
    assert with_details(p)["material"] == "帆布" and fake.calls["detail"] == 1   # cached


def test_expired_token_is_renewed_once(monkeypatch):
    fake = FakeYiwugo(expire_first_api_call=True)
    fresh_module(monkeypatch, fake)
    assert len(real_search("帆布袋")) == 1
    assert fake.calls["page"] == 2 and fake.calls["search"] == 2


def test_fen_is_yuan_on_the_page():
    assert yuan_from_fen(640) == 6.4
    assert yuan_from_fen(0) is None
    assert yuan_from_fen(None) is None


def test_listing_uses_seller_material_and_leaves_unknowns_empty():
    listing = live_listing()
    assert listing["live"] is True and listing["platform"] == "Yiwugo"
    assert listing["tiers"] == [(1000, 4.3)]
    assert listing["material"] == "帆布" and listing["size"] == "按要求定制"
    assert listing["weight_kg"] is None and listing["title_en"] is None
    assert listing["title_cn"] == "帆布手提袋"
    assert listing["supplier"]["years"] == 5 and listing["supplier"]["type"] is None
    assert listing["url"] == "https://www.yiwugo.com/product/detail/940179442.html"
    assert listing_from_api({"id": 1, "title": "无价", "sellPrice": None}, None) is None


def test_results_and_product_page_use_the_live_listing(no_ai):
    with mock.patch("core.yiwugo.search", return_value=[live_listing()]):
        results = page_text(run_app({"view": "results", "q": "帆布手提袋", "qty": "1000"}))
        detail = page_text(run_app({"view": "detail", "pid": "yw-940179442", "q": "帆布手提袋",
                                    "yq": "帆布手提袋", "qty": "1000"}))
    assert "¥4.30" in results and "/unit on Yiwugo" in results
    assert "<span class='src-tag live'>Live</span>" in results and "listings read from yiwugo.com" in results
    assert "Canvas tote bag" in results                                 # English name (glossary, no AI)
    assert "Live Yiwugo listing" in detail and "This listing has no weight" in detail
    assert "Category guessed from the title: bags" in detail


def test_live_listings_sorted_by_listing_price(no_ai):
    cheap = listing_from_api(dict(ITEM, id=1, sellPrice=200), None)
    dear = listing_from_api(dict(ITEM, id=2, sellPrice=350), None)
    with mock.patch("core.yiwugo.search", return_value=[dear, cheap]):
        t = page_text(run_app({"view": "results", "q": "帆布袋", "qty": "1000"}))
    assert t.index("¥2.00") < t.index("¥3.50")


def test_english_names_from_ai_when_available(no_ai):
    with mock.patch("core.yiwugo.search", return_value=[live_listing()]), \
         mock.patch.object(query_translation, "translate_titles",
                           return_value=(["Canvas tote bag, custom print"], None)):
        t = page_text(run_app({"view": "results", "q": "tote bag", "qty": "1000"}))
    assert "Canvas tote bag, custom print" in t


def test_buyer_weight_gives_the_delivered_price(no_ai):
    with mock.patch("core.yiwugo.search", return_value=[live_listing()]):
        at = run_app({"view": "detail", "pid": "yw-940179442", "q": "帆布手提袋", "yq": "帆布手提袋",
                      "qty": "1000"})
        at.number_input(key="lw_yw-940179442").set_value(180).run()
        assert not at.exception, at.exception
        t = page_text(at)
        assert "180 g <span class='tag tag-est'>user-provided</span>" in t
        assert "Total delivered" in t and not at.button(key="order_yw-940179442").disabled
        # the weight is reused in the results list: now a delivered price
        at.query_params.update({"view": "results"})
        at.session_state["view"] = "results"
        at.run()
        assert "/unit delivered" in page_text(at)


def test_marketplace_switches_can_show_only_real_yiwugo(no_ai):
    with mock.patch("core.yiwugo.search", return_value=[live_listing()]):
        at = run_app({"view": "results", "q": "tote bag", "qty": "1000"})
        assert page_text(at).count("<span class='src-tag'>Sample</span>") >= 1
        at.pills[0].set_value(["Yiwugo"]).run()
        assert not at.exception, at.exception
        only_yiwugo = page_text(at)
        assert only_yiwugo.count("class='mk'") == 1 and "¥4.30" in only_yiwugo
        assert "<span class='src-tag'>Sample</span>" not in only_yiwugo

        at = run_app({"view": "results", "q": "tote bag", "qty": "1000"})
        at.toggle[0].set_value(True).run()
        assert not at.exception, at.exception
        real = page_text(at)
        assert "<span class='src-tag live'>Live</span>" in real
        assert "<span class='src-tag'>Sample</span>" not in real
        assert "No real listings" not in real


def test_live_search_reports_failure_and_can_be_switched_off(no_ai, monkeypatch):
    with mock.patch("core.yiwugo.search", side_effect=TimeoutError()):
        t = page_text(run_app({"view": "results", "q": "tote bag"}))
    assert "Live Yiwugo listings: <span class='na'>not available</span> · Yiwugo did not respond (TimeoutError)" in t
    assert t.count("class='mk'") == 4                                    # sample catalog still shown
    assert t.count("<span class='src-tag'>Sample</span>") == 4          # ...and labelled as sample

    monkeypatch.setenv("YIWUGO_LIVE", "0")
    with mock.patch("core.yiwugo.search", side_effect=AssertionError("must not be called")):
        t = page_text(run_app({"view": "results", "q": "tote bag"}))
    assert "yiwugo.com" not in t and "Live Yiwugo" not in t
