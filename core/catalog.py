"""Product catalog: the team's padel racket listings in data/catalog_merged.json.

The file is kept exactly as the team delivers it; this module maps each record to the
product card the app uses. Fields set to null are genuinely unknown and are shown as
"not available". Records whose notes_en starts with "DEMO:" contain some made-up values
(the note lists which) and are labelled "demo data" in the app.
Photos: the record's `image` (e.g. images/1.jpg) lives in static/images/ and is served by
Streamlit at app/static/images/...; a missing photo gives a placeholder.
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "catalog_merged.json")
STATIC = os.path.join(ROOT, "static")

PLATFORMS = ["1688", "Taobao", "JD", "Pinduoduo"]
SELLER_TYPES = ["factory", "brand_official", "authorized_store", "trader"]

# category -> emoji + colour for the placeholder image
CATEGORY_STYLE = {
    "padel_racket": ("🎾", "#DCE8F5"),
    "unknown": ("📦", "#E0E0E0"),
}


def _image_url(path):
    """URL of the product photo, or None when the record has none or the file is missing."""
    if not path or not os.path.isfile(os.path.join(STATIC, path)):
        return None
    return "app/static/" + path.replace("\\", "/")


def _customisation(r):
    if r.get("customization_options_en"):
        return r["customization_options_en"]
    if r.get("customizable") is False:
        return "Not offered"
    return None


def to_card(r):
    """One record of catalog_merged.json -> the app's product card."""
    s = r.get("supplier") or {}
    notes = r.get("notes_en") or ""
    return {
        "id": str(r["id"]),
        "platform": r.get("platform"),
        "url": r.get("url"),
        "title_en": r.get("title_en"),
        "title_cn": r.get("title_original"),
        "keywords": "padel racket racquet paddle pala " + (r.get("material_en") or ""),
        "category": r.get("category"),
        "image": r.get("image"),
        "picture": _image_url(r.get("image")),
        "material": r.get("material_en"),
        "size": r.get("size"),
        "size_cm": r.get("size_cm"),
        "weight_kg": r.get("weight_kg"),
        "weight_includes_packaging": r.get("weight_includes_packaging"),
        "moq": r.get("moq"),
        "tiers": sorted((int(t["min_qty"]), float(t["price"])) for t in r.get("price_tiers_cny") or []),
        "production_days": r.get("lead_time_days"),
        "customisation": _customisation(r),
        "counterfeit_risk": bool(r.get("counterfeit_risk")),
        "notes": notes or None,
        "demo": notes.startswith("DEMO:"),
        "supplier": {
            "name": s.get("name_en"), "name_cn": s.get("name_original"), "city": s.get("city"),
            "type": s.get("seller_type"), "seller_type": s.get("seller_type"),
            "years": s.get("years_active"), "badges_cn": s.get("badges"), "store_type": s.get("store_type"),
            "taobao_credit_level": s.get("taobao_credit_level"),
            "service_scores_5pt": s.get("service_scores_5pt"),
            "positive_review_pct": s.get("positive_review_pct"),
            "repurchase_rate_pct": s.get("repurchase_rate_pct"),
            "sales_count": s.get("sales_count"), "sales_count_type": s.get("sales_count_type"),
        },
    }


def _load():
    with open(DATA, encoding="utf-8") as f:
        return [to_card(r) for r in json.load(f)]


PRODUCTS = _load()
_BY_ID = {p["id"]: p for p in PRODUCTS}


def get_product(pid):
    return _BY_ID.get(str(pid)) if pid is not None else None


def platform_from_url(url):
    """The marketplace a listing link belongs to (products 8-10 are labelled Pinduoduo but link to 1688)."""
    u = (url or "").lower()
    for key, name in [("1688.com", "1688"), ("taobao.com", "Taobao"), ("tmall.com", "Taobao"),
                      ("jd.com", "JD"), ("pinduoduo.com", "Pinduoduo"), ("yangkeduo.com", "Pinduoduo")]:
        if key in u:
            return name
    return None


def _norm_url(url):
    """Host + path without scheme and www/m., for matching pasted links."""
    u = re.sub(r"^https?://(www\.|m\.)?", "", (url or "").strip().lower())
    return u.split("#")[0].rstrip("/")


def _key(url):
    """Taobao/Tmall links identify the item by ?id=..., the others by the path."""
    u = _norm_url(url)
    m = re.search(r"[?&]id=(\d+)", u)
    return f"id={m.group(1)}" if m else u.split("?")[0]


def find_by_url(url):
    """The catalog product whose listing link matches a pasted URL (tracking parameters and
    the variant id are ignored), or None."""
    if not _norm_url(url):
        return None
    k = _key(url)
    return next((p for p in PRODUCTS if p.get("url") and _key(p["url"]) == k), None)


STOP = {"a", "an", "the", "for", "with", "and", "of", "to", "in", "custom", "cheap", "bulk"}


def search(query):
    """Keyword match over the catalog (whole words, plurals allowed)."""
    q = (query or "").lower().strip()
    if not q:
        return list(PRODUCTS)
    tokens = [t.rstrip("s") for t in q.replace(",", " ").split() if len(t) > 1]
    tokens = [t for t in tokens if t not in STOP] or tokens
    results = []
    for p in PRODUCTS:
        hay = f"{p['title_en']} {p['keywords']} {p['category'].replace('_', ' ')}".lower()
        # whole words only (plural allowed): "mat" must not match "matte"
        hits = sum(1 for t in tokens if re.search(r"\b" + re.escape(t) + r"(s|es)?\b", hay))
        if hits:
            results.append((hits, p))
    if not results:
        return []
    best = max(h for h, _ in results)
    # keep products that match at least half of the best hit count
    return [p for h, p in results if h >= max(1, best / 2)]
