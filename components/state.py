"""App state. The navigation state is mirrored in the URL, so links work on mobile
(a link reloads the page and the state comes back from the query string) and pages
can be shared. Conversations and orders are kept in JSON files for the demo."""

import os
from urllib.parse import urlencode

import streamlit as st

from core import messages as M
from core import orders as O
from core import profile as P
from core.catalog import get_product
from core.pricing import COUNTRIES, CURRENCIES

S = st.session_state

DEFAULTS = dict(view="home", tab="search", q="", qty=500, budget=0.0, country="Italy", cur="EUR",
                pid=None, cmp=[], conv=None, order=None)
VIEWS = ("home", "results", "detail", "compare", "paste", "inbox", "chat", "checkout", "orders", "profile")
TABS = ("link", "search", "messages")


def init_state():
    if S.get("_init"):
        return
    S._init = True
    qp = st.query_params
    for k, v in DEFAULTS.items():
        S[k] = v
    S.profile = P.load_profile()           # the buyer's defaults, overridden by the address
    if S.profile["country"] in COUNTRIES:
        S.country = S.profile["country"]
    if S.profile["currency"] in CURRENCIES:
        S.cur = S.profile["currency"]
    S.qty = max(1, int(S.profile["quantity"] or DEFAULTS["qty"]))
    try:
        if qp.get("view") in VIEWS:
            S.view = qp["view"]
        if qp.get("tab") in TABS:
            S.tab = qp["tab"]
        S.conv = qp.get("conv") or None
        S.order = qp.get("order") or None
        S.q = qp.get("q", "")
        S.qty = max(1, int(qp.get("qty", S.qty)))
        S.budget = max(0.0, float(qp.get("budget", 0)))
        if qp.get("country") in COUNTRIES:
            S.country = qp["country"]
        if qp.get("cur") in CURRENCIES:
            S.cur = qp["cur"]
        S.pid = qp.get("pid") or None
        S.cmp = [x for x in (qp.get("cmp") or "").split(",") if get_product(x)][:3]
    except (ValueError, TypeError):
        pass
    S.setdefault("pasted", None)
    S.setdefault("pasted_text", "")
    S.convs = M.load_conversations()   # demo storage: survives a page reload
    S.orders = O.load_orders()


def state_params(**over):
    p = dict(view=S.view, q=S.q, qty=S.qty, country=S.country, cur=S.cur)
    if S.view == "home" and S.tab != "search":
        p["tab"] = S.tab
    if S.budget:
        p["budget"] = S.budget
    if S.pid:
        p["pid"] = S.pid
    if S.cmp:
        p["cmp"] = ",".join(S.cmp)
    if S.conv and S.view == "chat":
        p["conv"] = S.conv
    if S.order and S.view in ("checkout", "orders"):
        p["order"] = S.order
    p.update(over)
    return {k: v for k, v in p.items() if v not in (None, "")}


def link(**over):
    return "?" + urlencode(state_params(**over))


def sync_url():
    want = {k: str(v) for k, v in state_params().items()}
    if dict(st.query_params) != want:
        st.query_params.from_dict(want)


def go(view, **kw):
    S.view = view
    for k, v in kw.items():
        S[k] = v


def bound(widget, label, name, **kw):
    """Widget whose value lives in S[name] and survives page changes."""
    wkey = f"_w_{name}"
    S[wkey] = S[name]

    def _copy():
        if S[wkey] is not None:  # e.g. a deselected segmented control keeps the old value
            S[name] = S[wkey]
    return widget(label, key=wkey, on_change=_copy, **kw)


def get_api_key():
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:  # no secrets.toml
        return None
