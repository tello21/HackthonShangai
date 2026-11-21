"""Sample catalog: loaded from data/catalog.json.

Every record is SAMPLE data written for the demo, not a live listing. Fields set to
null are genuinely unknown and are shown as "not available" in the app.
`demo_url` is a made-up link that Link paste recognises; it is not a real page.
"""

import json
import os
import re

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "catalog.json")

PLATFORMS = ["1688", "Taobao", "JD", "Pinduoduo"]
SELLER_TYPES = ["factory", "store", "middleman"]

# category -> emoji + colour for the placeholder image
CATEGORY_STYLE = {
    "bags": ("👜", "#E8D5B7"),
    "drinkware": ("🥤", "#BFDDF2"),
    "phone accessories": ("📱", "#D6CCF0"),
    "sports": ("🧘", "#C8E6C9"),
    "ceramics": ("☕", "#F3D3C6"),
    "lighting": ("💡", "#FFF1B8"),
    "unknown": ("📦", "#E0E0E0"),
}


def _load():
    with open(DATA, encoding="utf-8") as f:
        products = json.load(f)["products"]
    for p in products:
        p["tiers"] = [tuple(t) for t in p["tiers"]]
    return products


PRODUCTS = _load()
_BY_ID = {p["id"]: p for p in PRODUCTS}


def get_product(pid):
    return _BY_ID.get(pid)


def _norm_url(url):
    return re.sub(r"^https?://(www\.|m\.)?", "", (url or "").strip().lower()).rstrip("/")


def find_by_url(url):
    """The catalog product whose demo link matches a pasted URL, or None."""
    u = _norm_url(url)
    if not u:
        return None
    for p in PRODUCTS:
        if p.get("demo_url") and _norm_url(p["demo_url"]) in u:
            return p
    return None


STOP = {"a", "an", "the", "for", "with", "and", "of", "to", "in", "custom", "cheap", "bulk"}


def search(query):
    """Keyword match over the sample catalog (whole words, plurals allowed)."""
    q = (query or "").lower().strip()
    if not q:
        return list(PRODUCTS)
    tokens = [t.rstrip("s") for t in q.replace(",", " ").split() if len(t) > 1]
    tokens = [t for t in tokens if t not in STOP] or tokens
    results = []
    for p in PRODUCTS:
        hay = f"{p['title_en']} {p['keywords']} {p['category']}".lower()
        # whole words only (plural allowed): "mat" must not match "matte"
        hits = sum(1 for t in tokens if re.search(r"\b" + re.escape(t) + r"(s|es)?\b", hay))
        if hits:
            results.append((hits, p))
    if not results:
        return []
    best = max(h for h, _ in results)
    # keep products that match at least half of the best hit count
    return [p for h, p in results if h >= max(1, best / 2)]
