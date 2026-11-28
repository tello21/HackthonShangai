"""Scoutr — find it in China, see the real delivered price.

Run:  streamlit run app.py

Layout of the code:
  core/        business logic, no UI (catalog, pricing, supplier score, AI, messages, orders)
  components/  app state + URL, CSS, shared UI pieces
  views/       one module per page
  data/        sample catalog (JSON)
  tests/       pytest suite (python -m pytest)
"""

import streamlit as st

st.set_page_config(page_title="Scoutr – trusted suppliers in China, real delivered prices", page_icon="🔎", layout="centered",
                   initial_sidebar_state="collapsed")

from components import style  # noqa: E402  (set_page_config must run first)
from components.state import S, get_api_key, init_state, sync_url  # noqa: E402
from components.ui import nav_bar, scroll_to_top_on_view_change, site_footer  # noqa: E402
from core import ai  # noqa: E402
from core.pricing import refresh_fx  # noqa: E402
from views.checkout import page_checkout, page_orders  # noqa: E402
from views.compare import page_compare  # noqa: E402
from views.home import page_home  # noqa: E402
from views.link_analyzer import page_link  # noqa: E402
from views.messages import page_chat, page_inbox  # noqa: E402
from views.product import page_detail  # noqa: E402
from views.profile import page_profile  # noqa: E402
from views.results import page_results  # noqa: E402

init_state()
if S.view == "home" and S.tab == "messages":   # old address of the Messages tab
    S.view, S.tab = "inbox", "search"
if S.view == "paste" or S.tab == "link":       # old Link paste addresses -> Link analyzer
    S.view, S.tab = "link", "search"
if S.view == "orders" and not S.orders.get(S.order or ""):
    S.view = "profile"           # the order list lives in the profile
sync_url()
refresh_fx()                     # live ECB rates, at most every 6 h (15 min after a failure)
ai.set_api_key(get_api_key())
style.inject()
scroll_to_top_on_view_change()

PAGES = {"results": page_results, "detail": page_detail, "compare": page_compare, "link": page_link,
         "inbox": page_inbox, "chat": page_chat, "checkout": page_checkout, "orders": page_orders,
         "profile": page_profile}

if S.view in PAGES:
    nav_bar()
    PAGES[S.view]()
else:
    page_home()                  # draws the top bar itself
site_footer()
