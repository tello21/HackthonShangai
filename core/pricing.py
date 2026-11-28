"""Landed (delivered) cost of a product bought on a Chinese marketplace.

Built on the team's landed-cost model:
  - exchange rates live from the ECB (frankfurter API, free, no key), refreshed
    every 6 hours, with a fallback table when the request fails
  - four shipping modes (sea, rail, air, express) with transit times,
    volumetric weight, insurance and customs clearance
Changes for the site:
  - minimum chargeable weight per mode, so small orders are not priced at a
    fraction of a sea container
  - customs clearance depends on the mode (express couriers include it)
  - no made-up duty: an unknown category gives "not available"
  - missing data never hides the rest of the breakdown: each line can be None

Everything except the ECB rate is a SAMPLE ESTIMATE for the demo, not a quote.
Edit the tables to update them (EU duty rates: check TARIC).
"""

import json
import threading
import time
import urllib.request

# ---------------------------------------------------------------------------
# EXCHANGE RATES: 1 CNY in each currency
# ---------------------------------------------------------------------------

FALLBACK_FX = {
    "EUR": 0.12, "GBP": 0.105, "USD": 0.14, "CHF": 0.113, "NOK": 1.45, "SEK": 1.33,
    "DKK": 0.90, "PLN": 0.51, "CZK": 3.00, "HUF": 47.0, "RON": 0.61, "ISK": 17.4,
}
CURRENCIES = ["EUR", "GBP", "USD", "CHF", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RON", "ISK", "CNY"]
CURRENCY_NAMES = {
    "EUR": "Euro", "GBP": "British pound", "USD": "US dollar", "CHF": "Swiss franc",
    "SEK": "Swedish krona", "NOK": "Norwegian krone", "DKK": "Danish krone", "PLN": "Polish złoty",
    "CZK": "Czech koruna", "HUF": "Hungarian forint", "RON": "Romanian leu", "ISK": "Icelandic króna",
    "CNY": "Chinese yuan",
}
SYMBOL = {c: f"{c} " for c in CURRENCIES} | {"EUR": "€", "GBP": "£", "USD": "$", "CNY": "¥"}

FX_URLS = [
    "https://api.frankfurter.app/latest?from=CNY&to={symbols}",
    "https://api.frankfurter.dev/v1/latest?base=CNY&symbols={symbols}",
]
FX_OK_TTL = 6 * 3600      # keep a live rate for 6 hours
FX_FAIL_TTL = 15 * 60     # after a failure, retry in 15 minutes (never block every page)

_fx = dict(FALLBACK_FX, CNY=1.0)
_fx_info = {"source": "sample rate (live rate not loaded)", "date": None, "live": False}
_fx_checked = None
_fx_thread = None
_fx_lock = threading.Lock()


def _fetch_fx(timeout):
    symbols = ",".join(FALLBACK_FX)
    for url in FX_URLS:
        try:
            with urllib.request.urlopen(url.format(symbols=symbols), timeout=timeout) as r:
                data = json.loads(r.read().decode())
            rates = {cur: float(v) for cur, v in data["rates"].items() if cur in FALLBACK_FX}
            if rates:
                with _fx_lock:
                    _fx.update(rates)
                    _fx_info.update(source="ECB", date=data.get("date"), live=True)
                return
        except Exception:
            continue
    with _fx_lock:
        if not _fx_info["live"]:
            _fx_info.update(source="sample rate (live ECB rate unavailable)", date=None)


def refresh_fx(timeout=8, wait=False):
    """Refresh the ECB rates if they are stale. Safe to call on every page: the request runs in
    the background (the first request can take several seconds), so pages never wait for it;
    until it arrives the sample rates are used and labelled as such. wait=True blocks (tests)."""
    global _fx_checked, _fx_thread
    with _fx_lock:
        ttl = FX_OK_TTL if _fx_info["live"] else FX_FAIL_TTL
        fresh = _fx_checked is not None and time.monotonic() - _fx_checked < ttl
        running = _fx_thread is not None and _fx_thread.is_alive()
        if not fresh and not running:
            _fx_checked = time.monotonic()
            _fx_thread = threading.Thread(target=_fetch_fx, args=(timeout,), daemon=True)
            _fx_thread.start()
        thread = _fx_thread
    if wait and thread is not None:
        thread.join()
    return fx_info()


def fx_rate(currency):
    return _fx[currency]


def fx_info():
    return dict(_fx_info)


# ---------------------------------------------------------------------------
# COUNTRIES: local currency, VAT %, duty region, shipping zone
# ---------------------------------------------------------------------------

COUNTRIES = {
    "Italy":          {"currency": "EUR", "vat": 22.0, "duty": "EU", "zone": "EU"},
    "Germany":        {"currency": "EUR", "vat": 19.0, "duty": "EU", "zone": "EU"},
    "France":         {"currency": "EUR", "vat": 20.0, "duty": "EU", "zone": "EU"},
    "Spain":          {"currency": "EUR", "vat": 21.0, "duty": "EU", "zone": "EU"},
    "Portugal":       {"currency": "EUR", "vat": 23.0, "duty": "EU", "zone": "EU"},
    "Netherlands":    {"currency": "EUR", "vat": 21.0, "duty": "EU", "zone": "EU"},
    "Sweden":         {"currency": "SEK", "vat": 25.0, "duty": "EU", "zone": "EU"},
    "Denmark":        {"currency": "DKK", "vat": 25.0, "duty": "EU", "zone": "EU"},
    "Poland":         {"currency": "PLN", "vat": 23.0, "duty": "EU", "zone": "EU"},
    "Czech Republic": {"currency": "CZK", "vat": 21.0, "duty": "EU", "zone": "EU"},
    "Hungary":        {"currency": "HUF", "vat": 27.0, "duty": "EU", "zone": "EU"},
    "Romania":        {"currency": "RON", "vat": 21.0, "duty": "EU", "zone": "EU"},
    "United Kingdom": {"currency": "GBP", "vat": 20.0, "duty": "UK", "zone": "UK"},
    "Switzerland":    {"currency": "CHF", "vat": 8.1,  "duty": "CH", "zone": "EFTA"},
    "Norway":         {"currency": "NOK", "vat": 25.0, "duty": "NO", "zone": "EFTA"},
    "Iceland":        {"currency": "ISK", "vat": 24.0, "duty": "IS", "zone": "IS"},
    "United States":  {"currency": "USD", "vat": 0.0,  "duty": "US", "zone": "US"},
}

# ---------------------------------------------------------------------------
# IMPORT DUTY % by catalog category and duty region (sample values, verify)
# Switzerland has no duty on industrial goods since 2024; Norway and Iceland
# charge none on most industrial goods (textiles can be an exception).
# A category missing here gives "not available", never a guessed rate.
# ---------------------------------------------------------------------------

DUTY_RATES = {
    # rackets, HS 9506.59 ("other rackets", padel included)
    "padel_racket":      {"EU": 2.7, "UK": 2.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 4.0},
    "bags":             {"EU": 3.7, "UK": 4.0, "CH": 0.0, "NO": 8.0, "IS": 0.0, "US": 6.3},
    "drinkware":         {"EU": 3.2, "UK": 2.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 3.4},
    "sports":            {"EU": 2.7, "UK": 2.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 4.6},
    "lighting":          {"EU": 2.7, "UK": 2.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 3.9},
    "ceramics":          {"EU": 12.0, "UK": 12.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 6.0},
    "phone accessories": {"EU": 2.7, "UK": 2.0, "CH": 0.0, "NO": 0.0, "IS": 0.0, "US": 3.4},
}
DUTY = DUTY_RATES

# ---------------------------------------------------------------------------
# SHIPPING China -> buyer, door to door (estimates from 2026 market rates)
#
# Sources checked in November 2026 (forwarder rate guides and the Freightos/Xeneta air indices):
#   sea LCL China -> Europe   ~US$110-200 per m3 all-in (ocean + CFS/THC + docs), billed per m3
#                             or per 1,000 kg, whichever is higher, minimum 1 m3; 30-40 days port to port
#   rail LCL China -> Europe  ~US$160-210 per m3 (e.g. Xi'an -> Duisburg ~$185), 18-22 days terminal to terminal
#   air China -> Europe       ~US$3.9-6.6 per kg (index ~$4.9/kg, Nov 2026), volumetric 1:6000, 45 kg break
#   express (DHL/FedEx/UPS)   ~US$8-13 per kg for 10-25 kg, much more per kg for 1-2 kg parcels; door to door
# Converted at ~7.1 CNY per US$. Other zones: a multiplier on the Europe rate.
# These are averages: real quotes depend on the forwarder, the season and the exact box size.
# ---------------------------------------------------------------------------

MODES = ["express", "air", "rail", "sea"]
MODE_LABEL = {"sea": "Sea freight", "rail": "Rail freight", "air": "Air freight", "express": "Express courier"}
TRANSIT_DAYS = {"sea": "35–50", "rail": "20–30", "air": "6–10", "express": "3–7"}   # door to door

# sea and rail: billed per m3 (W/M: 1 m3 = this many kg, whichever is higher), minimum 1 m3
CNY_PER_M3 = {"sea": 1100.0, "rail": 1350.0}            # ~$155 and ~$190 per m3
KG_PER_M3 = {"sea": 1000, "rail": 500}
MIN_M3 = 1.0
# air and express: billed per chargeable kg (volumetric divisor in cm3 per kg)
CNY_PER_KG = {"air": 38.0, "express": 72.0}             # ~$5.3 and ~$10 per kg
VOLUMETRIC_DIVISOR = {"air": 6000, "express": 5000}
MIN_CHARGEABLE_KG = {"air": 45, "express": 0.5}
MIN_CHARGE_CNY = {"express": 280.0}                      # a 1 kg courier parcel costs ~$40
# per shipment: origin/destination handling, documents, delivery to the buyer's door
FIXED_CNY = {"sea": 1400.0, "rail": 1400.0, "air": 1000.0, "express": 0.0}
ZONE_FACTOR = {   # None = the mode doesn't serve this zone
    "sea":     {"EU": 1.0, "UK": 1.05, "EFTA": 1.15, "IS": 1.4, "US": 1.15},
    "rail":    {"EU": 1.0, "UK": 1.1, "EFTA": 1.1, "IS": None, "US": None},
    "air":     {"EU": 1.0, "UK": 1.05, "EFTA": 1.1, "IS": 1.25, "US": 1.05},
    "express": {"EU": 1.0, "UK": 1.0, "EFTA": 1.1, "IS": 1.25, "US": 1.0},
}
# Broker fee per shipment; express couriers clear customs as part of the service
CLEARANCE_CNY = {"sea": 600.0, "rail": 600.0, "air": 600.0, "express": 0.0}

DOMESTIC_CHINA_CNY_PER_KG = 2.0     # supplier -> forwarder warehouse (real weight)
INSURANCE_PCT = 0.5                 # % of goods value

# Box per unit when the listing gives no size (cm), so volume-billed freight is not underestimated
TYPICAL_BOX_CM = {"padel_racket": (50, 28, 5)}            # racket in its cover, retail box

ESTIMATE_NOTE = ("Freight uses 2026 market averages (sea ≈ $155/m³, rail ≈ $190/m³, air ≈ $5/kg, express ≈ $10/kg, "
                 "door to door): a reliable estimate, but still an estimate — a forwarder quote depends on the "
                 "season and the exact box size.")


# ---------------------------------------------------------------------------
# CALCULATION
# ---------------------------------------------------------------------------

def unit_price_cny(tiers, qty):
    """Tiers [(min_qty, price_cny), ...] -> unit price for this quantity."""
    if not tiers:
        return None
    tiers = sorted(tiers)
    price = tiers[0][1]
    for min_q, p in tiers:
        if qty >= min_q:
            price = p
    return price


def box_cm(product):
    """(box size per unit in cm, estimated?) — the listing's size, else the typical box of its category."""
    if product.get("size_cm"):
        return tuple(product["size_cm"]), False
    typical = TYPICAL_BOX_CM.get(product.get("category") or "")
    return (typical, True) if typical else (None, False)


def _sum(*vals):
    return None if any(v is None for v in vals) else sum(vals)


def _freight(product, qty, zone, mode):
    """(shipping CNY incl. China domestic transport, chargeable amount, unit 'kg'/'m3', minimum applied?)"""
    weight = product.get("weight_kg")
    if weight is None:
        return None, None, None, False
    factor = ZONE_FACTOR[mode][zone]
    kg = weight * qty
    box, _ = box_cm(product)
    m3 = None if box is None else box[0] * box[1] * box[2] * qty / 1e6
    domestic = kg * DOMESTIC_CHINA_CNY_PER_KG
    if mode in CNY_PER_M3:
        need = max(m3 or 0, kg / KG_PER_M3[mode])
        charged = max(need, MIN_M3)
        cost = charged * CNY_PER_M3[mode] * factor + FIXED_CNY[mode] + domestic
        return cost, charged, "m3", charged == MIN_M3 and need < MIN_M3
    need = max(kg, 0 if m3 is None else m3 * 1e6 / VOLUMETRIC_DIVISOR[mode])
    charged = max(need, MIN_CHARGEABLE_KG[mode])
    cost = max(charged * CNY_PER_KG[mode] * factor, MIN_CHARGE_CNY.get(mode, 0)) + FIXED_CNY[mode] + domestic
    return cost, charged, "kg", mode == "air" and need < MIN_CHARGEABLE_KG[mode]


def _landed_cny(product, qty, country, mode):
    """All amounts in CNY. Returns None if the mode doesn't serve this country."""
    c = COUNTRIES[country]
    if ZONE_FACTOR[mode][c["zone"]] is None:
        return None
    unit = unit_price_cny(product.get("tiers"), qty)
    goods = None if unit is None else unit * qty
    shipping, charged, charged_unit, min_applied = _freight(product, qty, c["zone"], mode)
    insurance = None if goods is None else goods * INSURANCE_PCT / 100
    clearance = CLEARANCE_CNY[mode]

    duty_pct = DUTY_RATES.get(product.get("category") or "", {}).get(c["duty"])
    if duty_pct is None or goods is None:
        duty = None
    elif c["duty"] == "US":                       # US: duty on goods value only
        duty = goods * duty_pct / 100
    else:                                         # elsewhere: on goods + freight + insurance
        base = _sum(goods, shipping, insurance)
        duty = None if base is None else base * duty_pct / 100
    vat_base = _sum(goods, shipping, insurance, duty, clearance)
    vat = None if vat_base is None else vat_base * c["vat"] / 100
    total = None if vat_base is None else vat_base + vat

    return dict(mode=mode, unit=unit, goods=goods, shipping=shipping, insurance=insurance,
                duty=duty, clearance=clearance, vat=vat, total=total, duty_pct=duty_pct,
                charged=charged, charged_unit=charged_unit, min_applied=min_applied)


def available_modes(country):
    zone = COUNTRIES[country]["zone"]
    return [m for m in MODES if ZONE_FACTOR[m][zone] is not None]


def delivered(product, qty, country, currency=None, mode="auto"):
    """Delivered cost in `currency` (default: the country's). mode="auto" picks the
    cheapest mode for this order. Any value can be None = not available."""
    c = COUNTRIES[country]
    currency = currency or c["currency"]
    fx = _fx[currency]
    qty = max(1, int(qty))

    options = [r for r in (_landed_cny(product, qty, country, m) for m in available_modes(country)) if r]
    if mode != "auto":
        chosen = next((r for r in options if r["mode"] == mode), None)
    else:
        priced = [r for r in options if r["total"] is not None]
        chosen = min(priced, key=lambda r: r["total"]) if priced else None
    if chosen is None:
        chosen = options[0]  # no full price possible: still show the partial breakdown
        mode_known = False
    else:
        mode_known = True

    def conv(v):
        return None if v is None else v * fx

    notes = []
    if product.get("moq") is not None and qty < product["moq"]:
        notes.append(f"Quantity below the MOQ of {product['moq']:,}: the lowest listed tier price is used")
    if chosen["min_applied"]:
        least = f"{MIN_M3:g} m³" if chosen["charged_unit"] == "m3" else f"{MIN_CHARGEABLE_KG[chosen['mode']]:,.0f} kg"
        notes.append(f"Small shipment: {MODE_LABEL[chosen['mode']].lower()} bills at least {least}")
    box, estimated = box_cm(product)
    if product.get("weight_kg") is not None and estimated:
        notes.append(f"Box size not in the listing: estimated {box[0]}×{box[1]}×{box[2]} cm per unit "
                     f"(typical box) for the volume")
    elif product.get("weight_kg") is not None and box is None:
        notes.append("Box size not available: volumetric weight not checked")
    if c["duty"] == "US":
        notes.append("US: state sales tax not included; extra tariffs on Chinese goods may apply")

    m = chosen["mode"]
    return dict(
        currency=currency, symbol=SYMBOL[currency], qty=qty, country=country,
        mode=m if mode_known else None, mode_label=MODE_LABEL[m], transit_days=TRANSIT_DAYS[m],
        unit_cny=chosen["unit"], below_moq=product.get("moq") is not None and qty < product["moq"],
        duty_pct=chosen["duty_pct"], duty_on_goods_only=c["duty"] == "US",
        vat_pct=c["vat"], tax_name="Sales tax (not included)" if c["duty"] == "US" else "VAT",
        product=conv(chosen["goods"]), shipping=conv(chosen["shipping"]),
        insurance=conv(chosen["insurance"]), duty=conv(chosen["duty"]),
        clearance=conv(chosen["clearance"]), vat=conv(chosen["vat"]), total=conv(chosen["total"]),
        per_unit=None if chosen["total"] is None else conv(chosen["total"]) / qty,
        product_per_unit=conv(chosen["unit"]),
        charged=chosen["charged"], charged_unit=chosen["charged_unit"], notes=notes,
        fx_rate=fx, fx=fx_info(),
    )


def compare_modes(product, qty, country, currency=None):
    """Delivered cost for every mode serving the country, cheapest first (unknown last)."""
    out = [delivered(product, qty, country, currency, m) for m in available_modes(country)]
    return sorted(out, key=lambda d: d["total"] if d["total"] is not None else float("inf"))
