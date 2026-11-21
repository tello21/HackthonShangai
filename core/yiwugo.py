"""Read listings from Yiwugo's public search (PR #1, Minghe Huang).

sellPrice on the search API is fen: 640 is ¥6.40 on the product page.
Fields the listing does not include stay None so the app can show "not available".

NOTE: this reads Yiwugo's website search endpoints, not an official API. It can stop
working whenever Yiwugo changes its site, and automated access may conflict with
Yiwugo's terms. Turn it off with the environment variable YIWUGO_LIVE=0: the app then
uses only the sample catalog.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def enabled() -> bool:
    """Live Yiwugo search is on unless YIWUGO_LIVE is 0 / false / off / no."""
    return os.getenv("YIWUGO_LIVE", "1").strip().lower() not in {"0", "false", "off", "no"}


def yuan_from_fen(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        yuan = round(float(value) / 100.0, 2)
    except (TypeError, ValueError):
        return None
    if yuan <= 0:
        return None
    return yuan


def _get(url: str, headers: dict | None = None, opener=None, timeout: int = 8) -> str:
    req_headers = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}
    if headers:
        req_headers.update(headers)
    request = urllib.request.Request(url, headers=req_headers)
    open_fn = opener.open if opener else urllib.request.urlopen
    with open_fn(request, timeout=timeout) as response:
        return response.read(120000).decode("utf-8", "replace")


def _is_ad(item: dict) -> bool:
    return str(item.get("isAd")).lower() in {"1", "true"}


def _attr(attrs: dict, names: tuple[str, ...]) -> str | None:
    for name in names:
        value = attrs.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def listing_from_api(item: dict, detail: dict | None) -> dict | None:
    """Catalog-shaped product. None when the search row has no positive price."""
    price = yuan_from_fen(item.get("sellPrice"))
    product_id = item.get("id")
    if price is None or not product_id:
        return None
    try:
        moq = int(item["startNum"]) if item.get("startNum") is not None else None
    except (TypeError, ValueError):
        moq = None
    attrs: dict[str, str] = {}
    years = None
    tiers: list[tuple[int, float]] = []
    if detail:
        inner = detail.get("detail") or {}
        for row in inner.get("productExtendList") or []:
            name = str(row.get("name") or "").strip()
            value = str(row.get("value") or "").strip()
            if name and value and name not in attrs:
                attrs[name] = value
        if detail.get("years") not in (None, ""):
            try:
                years = int(detail["years"])
            except (TypeError, ValueError):
                years = None
        for row in inner.get("sdiProductsPriceList") or []:
            fen = row.get("conferPrice")
            if fen in (None, 0, "0"):
                fen = row.get("sellPrice")
            yuan = yuan_from_fen(fen)
            if yuan is None:
                continue
            start = row.get("startNumber") or moq or 1
            try:
                start = int(start)
            except (TypeError, ValueError):
                start = moq or 1
            tiers.append((start, yuan))
    if not tiers:
        tiers = [(moq or 1, price)]
    title = str(item.get("title") or "").strip() or None
    shop = str(item.get("shopName") or "").strip() or None
    picture = str(item.get("picture1") or "").strip() or None
    return {
        "id": f"yw-{product_id}",
        "live": True,
        "platform": "Yiwugo",
        "category": None,
        "title_en": None,
        "title_cn": title,
        "keywords": title or "",
        "moq": moq,
        "tiers": tiers,
        "material": _attr(attrs, ("材质", "购物篮材质")),
        "size": _attr(attrs, ("尺寸", "规格", "尺码")),
        "weight_kg": None,
        "production_days": None,
        "customisation": _attr(attrs, ("加印LOGO", "加工定制")),
        "picture": picture,
        "url": f"https://www.yiwugo.com/product/detail/{product_id}.html",
        "supplier": {
            "name": shop,
            "name_cn": shop,
            "city": None,
            "type": None,
            "years": years,
            "badges": [],
            "response_rate": None,
            "repeat_buyer_rate": None,
            "disputes": None,
        },
    }


# ---------------------------------------------------------------------------
# Network. Every Yiwugo request takes ~5 s from Europe, so:
#  - the search token (CSRF + cookies) is fetched once, reused for 20 minutes,
#    and warmed up in the background when the app starts (warm_up)
#  - the list is built from the search rows alone; listing details (price tiers,
#    attributes, years) are fetched in the background and kept for 30 minutes
# ---------------------------------------------------------------------------

TOKEN_TTL = 20 * 60
DETAIL_TTL = 30 * 60
_lock = threading.Lock()
_token = None            # {"opener", "csrf", "referer", "at"}
_token_thread = None
_details: dict[str, tuple[float, dict | None]] = {}   # product id -> (time, detail)
_pool = ThreadPoolExecutor(max_workers=8)


def _new_token():
    page = "https://www.yiwugo.com/search?q=" + urllib.parse.quote("义乌")
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    match = re.search(r'"csrf":"([^"]+)"', _get(page, opener=opener))
    if not match:
        raise ValueError("no search token on the Yiwugo page")
    return {"opener": opener, "csrf": match.group(1), "referer": page, "at": time.monotonic()}


def _get_token(force=False):
    global _token
    with _lock:
        tok = _token
        thread = _token_thread
    if not force and tok and time.monotonic() - tok["at"] < TOKEN_TTL:
        return tok
    if not force and thread is not None and thread.is_alive():
        thread.join(timeout=12)          # the warm-up is already fetching it
        with _lock:
            tok = _token
        if tok and time.monotonic() - tok["at"] < TOKEN_TTL:
            return tok
    tok = _new_token()
    with _lock:
        _token = tok
    return tok


def warm_up():
    """Fetch the search token in the background (call at app start; never blocks)."""
    global _token_thread
    if not enabled():
        return

    def run():
        global _token
        try:
            tok = _new_token()
            with _lock:
                _token = tok
        except Exception:
            pass                          # the first search will try again

    with _lock:
        fresh = _token and time.monotonic() - _token["at"] < TOKEN_TTL
        running = _token_thread is not None and _token_thread.is_alive()
        if fresh or running:
            return
        _token_thread = threading.Thread(target=run, daemon=True)
        _token_thread.start()


def _api(url, tok):
    return _get(url, headers={"Referer": tok["referer"], "x-csrf-token": tok["csrf"],
                              "Accept": "application/json"}, opener=tok["opener"])


def _search_rows(query, tok):
    api = "https://www.yiwugo.com/api/search/s.htm?" + urllib.parse.urlencode({
        "q": query, "appid": "6", "cpage": "1", "pageSize": "20", "checkLabel": "1",
        "searchMethod": "embedding", "source": "pc",
    })
    content = json.loads(_api(api, tok)).get("content")
    if not isinstance(content, dict):
        raise ValueError("unexpected search answer")
    return content.get("prslist") or []


def _fetch_detail(product_id: str) -> dict | None:
    tok = _get_token()
    raw = _api(f"https://www.yiwugo.com/api/product/detail.htm?productId={product_id}", tok)
    content = json.loads(raw).get("content")
    detail = content if isinstance(content, dict) else None
    with _lock:
        _details[product_id] = (time.monotonic(), detail)
    return detail


def _cached_detail(product_id):
    with _lock:
        hit = _details.get(product_id)
    if hit and time.monotonic() - hit[0] < DETAIL_TTL:
        return True, hit[1]
    return False, None


def _offer(item, detail, has_detail):
    offer = listing_from_api(item, detail)
    if offer:
        offer["_row"] = item                      # kept to rebuild the listing with its details
        offer["details_loaded"] = has_detail
        market = str(item.get("marketOrAdress") or item.get("marketinfo") or "")
        sup = offer["supplier"]
        if market.startswith("义乌"):            # the shop's booth is in a Yiwu market
            sup["city"] = "Yiwu"
            offer["market"] = item.get("marketinfo") or market
        # trust score raw fields (core/scoring.py): a booth number means a physical stall
        sup["store_type"] = ("yiwugo_physical_stall" if item.get("boothNo") or market.startswith("义乌")
                             else "yiwugo_online_only")
        try:
            deals = item.get("dealQuantity")
            sup["sales_count"] = int(deals) if deals not in (None, "") else None
        except (TypeError, ValueError):
            sup["sales_count"] = None
    return offer


def search(query: str, limit: int = 8, details: bool = False) -> list[dict]:
    """Priced listings from the first page of Yiwugo search, in the site's order.
    details=False (default): built from the search rows at once; details are fetched in
    the background (prefetch) and used when available. details=True waits for them."""
    query = (query or "").strip()
    if not query:
        return []
    tok = _get_token()
    try:
        rows = _search_rows(query, tok)
    except (ValueError, json.JSONDecodeError, urllib.error.HTTPError):
        rows = _search_rows(query, _get_token(force=True))   # token expired: renew once
    chosen = []
    for item in rows:
        if _is_ad(item) or yuan_from_fen(item.get("sellPrice")) is None:
            continue
        chosen.append(item)
        if len(chosen) >= limit:
            break
    ids = [str(item["id"]) for item in chosen]
    if details:
        list(_pool.map(_safe_detail, ids))
    else:
        prefetch(ids)
    offers = []
    for item in chosen:
        has, detail = _cached_detail(str(item["id"]))
        offer = _offer(item, detail, has)
        if offer:
            offers.append(offer)
    return offers


def _safe_detail(product_id):
    try:
        return _fetch_detail(product_id)
    except Exception:
        return None


def details_ready(product_ids) -> bool:
    """True when every listing's details are in the cache (fetched or failed)."""
    return all(_cached_detail(str(pid))[0] for pid in product_ids)


def prefetch(product_ids):
    """Fetch listing details in the background (never blocks)."""
    for pid in product_ids:
        if not _cached_detail(pid)[0]:
            _pool.submit(_safe_detail, pid)


def with_details(offer: dict, wait: bool = True) -> dict:
    """The listing rebuilt with its details (price tiers, attributes, years)."""
    if offer.get("details_loaded") or not offer.get("_row"):
        return offer
    pid = str(offer["_row"]["id"])
    has, detail = _cached_detail(pid)
    if not has and wait:
        detail, has = _safe_detail(pid), True
    if not has:
        return offer
    rebuilt = _offer(offer["_row"], detail, True) or offer
    for key in ("title_en", "title_en_source", "category", "category_guessed"):
        if key in offer:
            rebuilt[key] = offer[key]
    return rebuilt
