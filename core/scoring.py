"""Supplier trust score, 0-100, comparable across 1688, Taobao, JD and Yiwugo.

Pure Python, no AI: the AI (or the listing parser) only extracts the raw fields;
this module turns them into the score, following the team's rules exactly.

Input per supplier (any field can be None):
  platform              "1688" | "Taobao" | "JD" | "Yiwugo"
  badges                list of str, e.g. 诚信通, 实力商家, 超级工厂, 实地认证, 深度验厂
  store_type            tmall_flagship | tmall | taobao_enterprise | taobao_personal |
                        jd_self_operated | jd_flagship | jd_third_party |
                        yiwugo_physical_stall | yiwugo_online_only
  years_active          number
  taobao_credit_level   "3_hearts", "2_diamonds", "4_crowns", "gold_crown"
  service_scores_5pt    list of numbers on a 5-point scale
  positive_review_pct   0-100
  repurchase_rate_pct   0-100
  seller_type           factory | brand_official | authorized_store | trader
  sales_count           number (counted differently per platform: never compared across platforms)
  unit_price            number, same currency for all results

score_suppliers(items) scores a whole search at once (sales percentile and price red flag
need the other results of the same platform); score_supplier(item) scores one alone.

Run the spec's test cases:  python core/scoring.py
"""

from __future__ import annotations

import math
import re
from statistics import median

WEIGHTS = {"Verification": 25, "Track record": 20, "Customer satisfaction": 25,
           "Loyalty": 10, "Seller type": 10, "Sales traction": 10}
MISSING = "Not available on this platform/listing"
MIN_COVERAGE = 0.40
MISSING_BASELINE = 40          # a missing metric counts as slightly below average
PRICE_FLAG_RATIO = 0.60
PRICE_FLAG_POINTS = 10
PRICE_FLAG_REASON = "Price much lower than similar listings on the same platform"

BANDS = [(80, "Trusted", "#3F7D20"), (60, "Good", "#8DB63C"), (40, "Caution", "#E0B000"), (0, "High risk", "#C62828")]
NO_DATA = ("Not enough data", "#9AA8B6")

# ---------------------------------------------------------------- 1. Verification (25)
BADGE_1688 = [("超级工厂", 100, "超级工厂 super factory badge"), ("实地认证", 100, "实地认证 on-site verified"),
              ("深度验厂", 100, "深度验厂 in-depth factory audit"), ("实力商家", 75, "实力商家 verified power merchant"),
              ("诚信通", 40, "Only 诚信通 membership")]
STORE_TYPES = {
    "Taobao": {"tmall_flagship": (100, "Tmall flagship store"), "tmall": (85, "Tmall store"),
               "taobao_enterprise": (55, "Taobao enterprise store"), "taobao_personal": (30, "Taobao personal store")},
    "JD": {"jd_self_operated": (100, "JD self-operated"), "jd_flagship": (80, "JD flagship store"),
           "jd_third_party": (50, "JD third-party seller")},
    "Yiwugo": {"yiwugo_physical_stall": (70, "Physical stall in Yiwu market"),
               "yiwugo_online_only": (40, "Online-only Yiwugo shop")},
}


def verification(f):
    platform = f.get("platform")
    if platform == "1688":
        badges = f.get("badges") or []
        hits = [(v, why) for name, v, why in BADGE_1688 if name in badges]
        if hits:
            return max(hits)                                     # the highest badge
        if f.get("badges") is None:
            return None, MISSING
        return 0, "No verification badge on 1688"
    table = STORE_TYPES.get(platform, {})
    if f.get("store_type") in table:
        return table[f["store_type"]]
    return None, MISSING


# ---------------------------------------------------------------- 2. Track record (20)
def _interp(x, points):
    """Linear interpolation over [(x, y), ...] sorted by x; clamps at both ends."""
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


YEARS = [(0, 0), (1, 25), (3, 60), (5, 80), (8, 100)]
CREDIT_BASE = {"heart": 5, "diamond": 35, "crown": 65}          # level n -> base + 5n (1..5)


def credit_value(level):
    if not level:
        return None
    s = str(level).strip().lower()
    if s.replace(" ", "_") == "gold_crown":
        return 100
    m = re.fullmatch(r"([1-5])[_ ]?(heart|diamond|crown)s?", s)
    return CREDIT_BASE[m.group(2)] + 5 * int(m.group(1)) if m else None


def _plural(n, word):
    return f"{n:g} {word}{'' if n == 1 else 's'}"


def track_record(f):
    years, credit = f.get("years_active"), credit_value(f.get("taobao_credit_level"))
    parts, why = [], []
    if years is not None:
        parts.append(_interp(float(years), YEARS))
        why.append(f"{_plural(float(years), 'year')} on {f.get('platform') or 'the platform'}")
    if credit is not None:
        parts.append(credit)
        why.append(f"{str(f['taobao_credit_level']).replace('_', ' ')} seller credit")
    if not parts:
        return None, MISSING
    return sum(parts) / len(parts), " · ".join(why)


# ---------------------------------------------------------------- 3. Customer satisfaction (25)
def satisfaction(f):
    parts, why = [], []
    scores = [s for s in (f.get("service_scores_5pt") or []) if s is not None]
    if scores:
        avg = sum(scores) / len(scores)
        parts.append(_interp(avg, [(4.0, 0), (5.0, 100)]))
        why.append(f"Service rating {avg:.1f}/5")
    if f.get("positive_review_pct") is not None:
        parts.append(_interp(float(f["positive_review_pct"]), [(90, 0), (100, 100)]))
        why.append(f"{f['positive_review_pct']:g}% positive reviews")
    if not parts:
        return None, MISSING
    return sum(parts) / len(parts), " · ".join(why)


# ---------------------------------------------------------------- 4. Loyalty (10)
def loyalty(f):
    r = f.get("repurchase_rate_pct")
    if r is None:
        return None, MISSING
    return _interp(float(r), [(0, 0), (50, 100)]), f"{r:g}% repurchase rate"


# ---------------------------------------------------------------- 5. Seller type (10)
SELLER_TYPES = {"factory": (100, "Factory (manufacturer)"), "brand_official": (100, "Brand official store"),
                "authorized_store": (70, "Authorized store"), "trader": (40, "Trading company")}


def seller_type(f):
    t = f.get("seller_type")
    if t is None and f.get("platform") == "JD" and f.get("store_type") == "jd_self_operated":
        t = "brand_official"
    if t in SELLER_TYPES:
        return SELLER_TYPES[t]
    return None, MISSING


# ---------------------------------------------------------------- 6. Sales traction (10)
SALES_TIERS = [(0, 0), (1, 20), (2, 40), (3, 70), (4, 100)]    # on log10(sales): 1, 10, 100, 1,000, 10,000


def _percentile(value, values):
    """Percentile rank of value among values (ties count half), 0-100."""
    others = list(values)
    others.remove(value)
    below = sum(1 for v in others if v < value)
    equal = sum(1 for v in others if v == value)
    return 100 * (below + 0.5 * equal) / len(others)


def sales_traction(f, same_platform_sales=None):
    n = f.get("sales_count")
    if n is None:
        return None, MISSING
    n = max(0.0, float(n))
    if same_platform_sales is not None and len(same_platform_sales) >= 3:
        pct = _percentile(n, same_platform_sales)
        where = f"{f.get('platform')} results in this search"
        if pct >= 50:
            return pct, f"{n:,.0f} sales — more than {pct:.0f}% of {where}"
        return pct, f"{n:,.0f} sales — fewer than {100 - pct:.0f}% of {where}"
    value = 0.0 if n < 1 else _interp(math.log10(n), SALES_TIERS)   # 0 sales -> 0
    return value, f"{n:,.0f} sales/orders"


METRICS = [("Verification", verification), ("Track record", track_record),
           ("Customer satisfaction", satisfaction), ("Loyalty", loyalty), ("Seller type", seller_type)]


# ---------------------------------------------------------------- scoring
def _round(x):
    return int(math.floor(x + 0.5))


def band_of(score):
    if score is None:
        return NO_DATA
    for low, name, colour in BANDS:
        if score >= low:
            return name, colour
    return BANDS[-1][1:]


def score_supplier(f, peers_sales=None, peers_prices=None):
    """Score one supplier. peers_* = values of the same platform in the current search
    (including this one); without them sales use log tiers and no price flag applies."""
    metrics = []
    for name, fn in METRICS:
        value, reason = fn(f)
        metrics.append({"name": name, "weight": WEIGHTS[name], "value": value, "reason": reason})
    value, reason = sales_traction(f, peers_sales)
    metrics.append({"name": "Sales traction", "weight": WEIGHTS["Sales traction"], "value": value, "reason": reason})

    available = [m for m in metrics if m["value"] is not None]
    covered = sum(m["weight"] for m in available)
    coverage = covered / 100
    for m in metrics:
        if m["value"] is not None:
            m["value"] = _round(m["value"])

    result = {"score": None, "band": NO_DATA[0], "colour": NO_DATA[1], "coverage_pct": _round(coverage * 100),
              "metrics": metrics, "penalties": [], "reasons": [],
              "missing": [m["name"] for m in metrics if m["value"] is None]}
    if coverage < MIN_COVERAGE:
        result["reasons"] = [f"Not enough public data ({result['coverage_pct']}% coverage)"] + \
                            [f"{m} unknown" for m in result["missing"][:3]]
        return result

    raw = sum(m["value"] * m["weight"] for m in available) / covered
    final = coverage * raw + (1 - coverage) * MISSING_BASELINE

    # price red flag (not for 1688)
    price = f.get("unit_price")
    if (f.get("platform") != "1688" and price is not None and peers_prices is not None
            and len(peers_prices) >= 3 and price < PRICE_FLAG_RATIO * median(peers_prices)):
        final -= PRICE_FLAG_POINTS
        result["penalties"].append(PRICE_FLAG_REASON)

    score = max(0, min(100, _round(final)))
    result["score"] = score
    result["band"], result["colour"] = band_of(score)
    result["reasons"] = _card_reasons(metrics, result["penalties"])
    return result


NEGATIVE_WHEN_MISSING = {"Customer satisfaction": "No customer ratings available",
                         "Track record": "Years active unknown", "Verification": "No verification data",
                         "Loyalty": "No repurchase data", "Seller type": "Seller type unknown",
                         "Sales traction": "No sales data"}


def _card_reasons(metrics, penalties):
    """3-4 short strings: strongest positive and negative signals, alternating."""
    positives = sorted((m for m in metrics if m["value"] is not None and m["value"] >= 60),
                       key=lambda m: -(m["value"] * m["weight"]))
    negatives = [(-(100 - m["value"]) * m["weight"], m["reason"])
                 for m in metrics if m["value"] is not None and m["value"] < 50]
    negatives += [(-60 * m["weight"], NEGATIVE_WHEN_MISSING[m["name"]]) for m in metrics if m["value"] is None]
    negatives = [why for _, why in sorted(negatives)]
    negatives = penalties + negatives
    out = []
    for i in range(2):
        if i < len(positives):
            out.append(positives[i]["reason"])
        if i < len(negatives):
            out.append(negatives[i])
    return out[:4]


def score_suppliers(items):
    """Score all results of one search. items: dicts with an 'id' and the raw fields.
    Returns {id: result}. Sales and prices are only compared within the same platform."""
    by_platform = {}
    for it in items:
        by_platform.setdefault(it.get("platform"), []).append(it)
    out = {}
    for platform, group in by_platform.items():
        sales = [float(g["sales_count"]) for g in group if g.get("sales_count") is not None]
        prices = [float(g["unit_price"]) for g in group if g.get("unit_price") is not None]
        for it in group:
            out[it["id"]] = score_supplier(
                it,
                peers_sales=sales if it.get("sales_count") is not None and len(sales) >= 3 else None,
                peers_prices=prices if len(prices) >= 3 else None)
    return out


# ---------------------------------------------------------------- the spec's test cases
def _cases():
    super_factory = score_supplier({"platform": "1688", "badges": ["诚信通", "超级工厂"], "years_active": 8,
                                    "service_scores_5pt": [4.8], "repurchase_rate_pct": 45,
                                    "seller_type": "factory", "sales_count": 2000})
    jd_self = score_supplier({"platform": "JD", "store_type": "jd_self_operated", "positive_review_pct": 98,
                              "sales_count": 50000})
    taobao_personal = score_supplier({"platform": "Taobao", "store_type": "taobao_personal",
                                      "taobao_credit_level": "2_hearts", "service_scores_5pt": [4.6],
                                      "seller_type": "trader"})
    stall = score_supplier({"platform": "Yiwugo", "store_type": "yiwugo_physical_stall", "years_active": 3})
    online = score_supplier({"platform": "Yiwugo", "store_type": "yiwugo_online_only"})
    return super_factory, jd_self, taobao_personal, stall, online


def run_tests():
    sf, jd, tb, stall, online = _cases()
    assert sf["band"] == "Trusted" and sf["score"] == 92 and sf["coverage_pct"] == 100, sf
    assert jd["score"] == 77 and jd["score"] < sf["score"] and jd["coverage_pct"] == 70, jd
    # NOTE: the spec expects "Caution" here, but its own rules give 37.5 -> 38 = "High risk":
    # verification 30, credit 15, DSR 4.6 -> 60, trader 40, coverage 80% -> 0.8*36.9 + 0.2*40
    assert tb["score"] == 38 and tb["band"] == "High risk", tb
    assert stall["score"] == 52 and stall["band"] == "Caution" and stall["coverage_pct"] == 45, stall
    assert stall["score"] < sf["score"]
    assert online["score"] is None and online["band"] == "Not enough data" and online["coverage_pct"] == 25, online

    # shared rules
    assert credit_value("gold_crown") == 100 and credit_value("2_diamonds") == 45 and credit_value("1_hearts") == 10
    assert _interp(2, YEARS) == 42.5
    batch = score_suppliers([
        {"id": "a", "platform": "Taobao", "store_type": "tmall", "years_active": 5, "sales_count": 10, "unit_price": 10},
        {"id": "b", "platform": "Taobao", "store_type": "tmall", "years_active": 5, "sales_count": 100, "unit_price": 10},
        {"id": "c", "platform": "Taobao", "store_type": "tmall", "years_active": 5, "sales_count": 1000, "unit_price": 4},
        {"id": "d", "platform": "1688", "badges": ["诚信通"], "sales_count": 5, "unit_price": 1},
    ])
    assert batch["c"]["metrics"][5]["value"] == 100 and batch["a"]["metrics"][5]["value"] == 0   # percentile
    assert batch["c"]["penalties"] == [PRICE_FLAG_REASON] and not batch["a"]["penalties"]       # 4 < 0.6 * 10
    assert batch["d"]["metrics"][5]["value"] == _round(20 * math.log10(5))                       # 1688 alone: log tiers
    return sf, jd, tb, stall, online


if __name__ == "__main__":
    for label, r in zip(["1688 super factory", "JD self-operated", "Taobao personal", "Yiwugo stall",
                         "Yiwugo online only"], run_tests()):
        print(f"{label:20} score={r['score']!s:>4}  band={r['band']:16} coverage={r['coverage_pct']}%  "
              f"reasons={r['reasons']}")
    print("all scoring tests passed")
