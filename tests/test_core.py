"""Business logic: catalog, delivered price, supplier score, orders."""

from core import orders as O
from core import pricing as P
from core.catalog import PRODUCTS, get_product, platform_from_url, search
from core.supplier_score import trust_for, trust_for_search


# ---------------------------------------------------------------- catalog
def test_catalog_maps_the_team_file():
    assert len(PRODUCTS) == 13 and [p["id"] for p in PRODUCTS] == [str(i) for i in range(1, 14)]
    p1 = get_product(1)
    assert p1["tiers"] == [(2, 140.0), (50, 128.0), (200, 115.0)] and p1["production_days"] == 30
    assert p1["supplier"]["badges_cn"] == ["诚信通", "超级工厂"] and p1["demo"] is True
    assert get_product("6")["demo"] is False and get_product("2")["counterfeit_risk"] is True
    assert {p["platform"] for p in PRODUCTS if p["id"] in ("8", "9", "10")} == {"Pinduoduo"}
    assert p1["picture"] == "app/static/images/1.jpg"
    assert get_product("7")["customisation"] == "Not offered"           # customizable: false


def test_missing_photo_gives_placeholder():
    from components.ui import image_uri
    from core.catalog import to_card
    rec = {"id": 99, "image": "images/does-not-exist.jpg", "category": "padel_racket"}
    assert to_card(rec)["picture"] is None and to_card(dict(rec, image=None))["picture"] is None
    assert image_uri(to_card(rec)).startswith("data:image/svg+xml")
    assert image_uri(get_product("1")) == "app/static/images/1.jpg"


def test_search_whole_words():
    assert [p["id"] for p in search("beginner")] == ["12"]
    assert len(search("padel rackets")) == 13
    assert search("laptop") == []
    assert len(search("")) == len(PRODUCTS)


def test_listing_links_name_their_marketplace():
    assert platform_from_url(get_product("8")["url"]) == "1688"          # labelled Pinduoduo, links to 1688
    assert platform_from_url("https://item.taobao.com/item.htm?id=1") == "Taobao"
    assert platform_from_url("https://item.jd.com/1.html") == "JD" and platform_from_url("") is None


# ---------------------------------------------------------------- delivered price
def test_cheapest_mode_depends_on_quantity():
    p = get_product("3")
    assert P.delivered(p, 1, "Italy", "EUR")["mode"] == "express"       # minimum charges make sea absurd
    assert P.delivered(p, 5000, "Italy", "EUR")["mode"] == "sea"
    modes = P.compare_modes(p, 500, "Italy", "EUR")
    assert [m["per_unit"] for m in modes] == sorted(m["per_unit"] for m in modes)


def test_breakdown_adds_up():
    d = P.delivered(get_product("3"), 500, "Italy", "EUR", "air")
    parts = d["product"] + d["shipping"] + d["insurance"] + d["duty"] + d["clearance"] + d["vat"]
    assert abs(parts - d["total"]) < 1e-6
    assert abs(d["vat"] - 0.22 * (d["total"] - d["vat"])) < 1e-6
    assert d["duty_pct"] == 2.7                                         # padel racket, EU


def test_missing_data_is_not_invented():
    no_weight = P.delivered(get_product("11"), 500, "Italy", "EUR")    # Taobao listing without weight
    assert no_weight["product"] is not None and no_weight["shipping"] is None and no_weight["total"] is None
    unknown_cat = P.delivered(dict(get_product("3"), category="toys"), 500, "Italy")
    assert unknown_cat["duty"] is None and unknown_cat["total"] is None


def test_express_includes_clearance_and_us_has_no_vat():
    assert P.delivered(get_product("3"), 1, "Italy", "EUR", "express")["clearance"] == 0
    us = P.delivered(get_product("3"), 500, "United States", "USD")
    assert us["vat"] == 0 and us["tax_name"].startswith("Sales tax")


def test_fx_refresh_never_blocks_and_falls_back(monkeypatch):
    import time
    monkeypatch.setattr(P, "_fx_checked", None)
    monkeypatch.setattr(P, "_fx_info", dict(P._fx_info, live=False))
    t = time.time()
    P.refresh_fx()                                  # returns at once, request runs in the background
    assert time.time() - t < 0.5
    info = P.refresh_fx(wait=True)                  # FX_URLS is empty in tests: sample rate
    assert info["live"] is False and "sample rate" in info["source"]


# ---------------------------------------------------------------- supplier score
def test_scoring_spec_cases():
    from core import scoring
    scoring.run_tests()                    # the five cases from the spec + shared rules (python core/scoring.py)


def test_trust_for_the_padel_catalog():
    """Every supplier scored as one search (as on the results page), the team's catalog."""
    from core.scoring import COUNTERFEIT_REASON, PRICE_FLAG_REASON
    res = trust_for_search([(p, P.delivered(p, 500, "Italy", "EUR")["unit_cny"]) for p in PRODUCTS])
    got = {pid: (r["score"], r["band"]) for pid, r in res.items()}
    assert got == {"1": (94, "Trusted"), "2": (24, "High risk"), "3": (72, "Good"), "4": (54, "Caution"),
                   "5": (68, "Good"), "6": (48, "Caution"), "7": (25, "High risk"), "8": (66, "Good"),
                   "9": (43, "Caution"), "10": (38, "High risk"), "11": (None, "Not enough data"),
                   "12": (None, "Not enough data"), "13": (None, "Not enough data")}
    assert res["2"]["reasons"][0] == COUNTERFEIT_REASON                  # counterfeit: first reason, -30
    assert res["6"]["penalties"] == [PRICE_FLAG_REASON]                  # 298 < 60% of the JD median
    assert res["8"]["penalties"] == [PRICE_FLAG_REASON] and res["8"]["metrics"][0]["value"] is None  # Pinduoduo
    assert not res["7"]["penalties"]                                     # no price flag on 1688
    alone = trust_for(get_product("2"), 125)          # alone: sales on the log scale, same counterfeit rule
    assert alone["penalties"] == [COUNTERFEIT_REASON] and alone["band"] == "High risk"
    # a listing that only tells the shop name: not enough data, no neutral-looking number
    bare = trust_for({"id": "x", "platform": "Pinduoduo", "supplier": {"name": "某店"}})
    assert bare["score"] is None and bare["band"] == "Not enough data"


def test_price_red_flag_only_within_the_same_platform():
    def taobao(pid, price):
        return ({"id": pid, "platform": "Taobao", "supplier": {"store_type": "tmall", "years": 5}}, price)
    res = trust_for_search([taobao("a", 10), taobao("b", 11), taobao("c", 4),
                            ({"id": "d", "platform": "1688", "supplier": {"badges_cn": ["实力商家"], "years": 5}}, 1)])
    assert res["c"]["penalties"] and not res["a"]["penalties"] and not res["d"]["penalties"]


# ---------------------------------------------------------------- orders
def test_order_flow_and_amounts():
    p = get_product("3")
    d = P.delivered(p, 500, "Italy", "EUR")
    o = O.new_order(p, 500, "Italy", "EUR", d, None, False)
    assert abs(o["deposit"] - 0.3 * d["product"]) < 1e-9
    assert abs(o["deposit"] + o["balance"] + o["on_arrival"] - d["total"]) < 1e-6
    O.pay_balance(o)                     # not allowed before the deposit
    assert o["status"] == "placed" and not o["payments"]
    for step in (O.pay_deposit, O.finish_production, O.pay_balance, O.ship):
        step(o)
    assert o["status"] == "shipped"
    assert abs(O.paid_total(o) - d["product"]) < 1e-6
    assert all(pay["ref"].startswith("SIM-") for pay in o["payments"])
