"""Bridge between our product cards and core/scoring.py.

Product cards come from the catalog. This
module only maps their supplier data to scoring.py's raw fields; the score itself is
computed by scoring.py (pure rules, see that file).
"""

from core import scoring

# English badge names used by older data / the rule-based parser -> the platform's Chinese badge
EN_TO_CN_BADGE = {"Verified supplier": "实力商家", "Onsite inspection": "实地认证", "Source factory": "超级工厂",
                  "TrustPass member": "诚信通", "In-depth factory audit": "深度验厂", "Super factory": "超级工厂"}
OLD_TYPE = {"factory": "factory", "middleman": "trader"}


def raw_fields(p, unit_price=None):
    """scoring.py input for one product card (None where the listing doesn't say)."""
    s = p.get("supplier") or {}
    badges = s.get("badges_cn")
    if badges is None and s.get("badges"):
        badges = [EN_TO_CN_BADGE[b] for b in s["badges"] if b in EN_TO_CN_BADGE] or None
    store_type = s.get("store_type")
    if store_type is None and p.get("platform") == "JD":
        if "Platform self-operated" in (s.get("badges") or []):
            store_type = "jd_self_operated"
        elif "Brand official store" in (s.get("badges") or []):
            store_type = "jd_flagship"
    repurchase = s.get("repurchase_rate_pct")
    if repurchase is None:
        repurchase = s.get("repeat_buyer_rate")
    return {
        "id": p.get("id"),
        "platform": p.get("platform"),
        "badges": badges,
        "store_type": store_type,
        "years_active": s.get("years"),
        "taobao_credit_level": s.get("taobao_credit_level"),
        "service_scores_5pt": s.get("service_scores_5pt"),
        "positive_review_pct": s.get("positive_review_pct"),
        "repurchase_rate_pct": repurchase,
        "seller_type": s.get("seller_type") or OLD_TYPE.get(s.get("type")),
        "sales_count": s.get("sales_count"),
        "unit_price": unit_price,
        "counterfeit_risk": bool(p.get("counterfeit_risk")),
    }


def trust_for_search(rows):
    """rows: [(product, unit_price_cny), ...] of one search -> {product id: scoring result}."""
    return scoring.score_suppliers([raw_fields(p, price) for p, price in rows])


def trust_for(p, unit_price=None):
    """One product scored on its own (no other results to compare sales or price with)."""
    return scoring.score_supplier(raw_fields(p, unit_price))
