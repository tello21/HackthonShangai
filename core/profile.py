"""Buyer profile: name, company, contact and search defaults (country, currency, quantity).

Demo storage in profile.json (git-ignored), one profile for the whole demo, like orders.
The defaults are used when a page opens without them in the address.
"""

import json
import os
import re

STORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profile.json")

FIELDS = {"name": "", "company": "", "email": "", "country": "Italy", "currency": "EUR", "quantity": 500}


def load_profile():
    try:
        with open(STORE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    return {k: data.get(k, v) for k, v in FIELDS.items()} if isinstance(data, dict) else dict(FIELDS)


def validate(p):
    """List of problems (empty when the profile can be saved)."""
    errors = []
    if p.get("email") and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", p["email"]):
        errors.append("The email address doesn't look right.")
    if int(p.get("quantity") or 0) < 1:
        errors.append("The default quantity must be at least 1.")
    return errors


def save_profile(p):
    clean = {k: p.get(k, v) for k, v in FIELDS.items()}
    clean["quantity"] = int(clean["quantity"])
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=1)
    os.replace(tmp, STORE)
    return clean


def initials(p):
    parts = [w for w in re.split(r"\s+", (p.get("name") or "").strip()) if w]
    return "".join(w[0].upper() for w in parts[:2]) or "?"
