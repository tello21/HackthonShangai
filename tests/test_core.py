"""Business logic: catalog, delivered price, supplier score, orders."""

from core import orders as O
from core import pricing as P
from core.catalog import PRODUCTS, find_by_url, get_product, search
from core.supplier_score import trust_for, trust_for_search


# ---------------------------------------------------------------- catalog
def test_search_whole_words():
    assert [p["id"] for p in search("yoga mat")] == ["YM-01", "YM-02", "YM-03"]   # not "matte" mugs
    assert len(search("water bottles")) == 4
    assert search("laptop") == []
    assert len(search("")) == len(PRODUCTS) == 20


def test_find_by_demo_url():
    assert find_by_url("https://detail.1688.com/offer/demo-tb-01.html?spm=abc")["id"] == "TB-01"
    assert find_by_url("item.taobao.com/item.htm?id=demo-tb-04")["id"] == "TB-04"
    assert find_by_url("https://detail.1688.com/offer/612345.html") is None
    assert find_by_url("") is None


# ---------------------------------------------------------------- delivered price
def test_cheapest_mode_depends_on_quantity():
    p = get_product("WB-01")
    assert P.delivered(p, 1, "Italy", "EUR")["mode"] == "express"       # minimum charges make sea absurd
    assert P.delivered(p, 5000, "Italy", "EUR")["mode"] == "sea"
    modes = P.compare_modes(p, 500, "Italy", "EUR")
    assert [m["per_unit"] for m in modes] == sorted(m["per_unit"] for m in modes)


def test_breakdown_adds_up():
    d = P.delivered(get_product("WB-01"), 500, "Italy", "EUR", "air")
    parts = d["product"] + d["shipping"] + d["insurance"] + d["duty"] + d["clearance"] + d["vat"]
    assert abs(parts - d["total"]) < 1e-6
    assert abs(d["vat"] - 0.22 * (d["total"] - d["vat"])) < 1e-6


def test_missing_data_is_not_invented():
    no_weight = P.delivered(get_product("TB-04"), 500, "Italy", "EUR")
    assert no_weight["product"] is not None and no_weight["shipping"] is None and no_weight["total"] is None
    unknown_cat = P.delivered(dict(get_product("WB-01"), category="toys"), 500, "Italy")
    assert unknown_cat["duty"] is None and unknown_cat["total"] is None


def test_express_includes_clearance_and_us_has_no_vat():
    assert P.delivered(get_product("WB-01"), 1, "Italy", "EUR", "express")["clearance"] == 0
    us = P.delivered(get_product("WB-01"), 500, "United States", "USD")
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


def test_trust_for_catalog_products():
    mg01 = trust_for(get_product("MG-01"), 3.1)          # 1688, 实地认证, 18 years, 45% repurchase
    assert mg01["band"] == "Trusted" and mg01["coverage_pct"] == 100
    wb04 = trust_for(get_product("WB-04"), 6.3)          # 1688 trader, only 诚信通, 2 years, 9% repurchase
    assert wb04["band"] == "High risk"
    assert "Only 诚信通 membership" in [m["reason"] for m in wb04["metrics"]]
    jd = trust_for(get_product("MG-03"), 62)             # JD self-operated: seller type counts as brand official
    assert jd["metrics"][4]["value"] == 100 and jd["metrics"][4]["reason"] == "Brand official store"
    # a live listing that only tells the shop name: not enough data, no neutral-looking number
    bare = trust_for({"id": "x", "platform": "Yiwugo", "supplier": {"name": "某店"}})
    assert bare["score"] is None and bare["band"] == "Not enough data"


def test_price_red_flag_only_within_the_same_platform():
    def taobao(pid, price):
        return ({"id": pid, "platform": "Taobao", "supplier": {"store_type": "tmall", "years": 5}}, price)
    res = trust_for_search([taobao("a", 10), taobao("b", 11), taobao("c", 4),
                            ({"id": "d", "platform": "1688", "supplier": {"badges_cn": ["实力商家"], "years": 5}}, 1)])
    assert res["c"]["penalties"] and not res["a"]["penalties"] and not res["d"]["penalties"]


# ---------------------------------------------------------------- orders
def test_order_flow_and_amounts():
    p = get_product("WB-01")
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
