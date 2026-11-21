"""SourceScan — find it in China, see the real delivered price.

Run:  streamlit run app.py

Layout of the code:
  core/        business logic, no UI (catalog, pricing, supplier score, AI, messages, orders, listing)
  components/  app state + URL, CSS, shared UI pieces
  views/       one module per page
  data/        sample catalog (JSON)
  tests/       pytest suite (python -m pytest)
"""

import streamlit as st

st.set_page_config(page_title="SourceScan – trusted suppliers in China, real delivered prices", page_icon="🔎", layout="centered",
                   initial_sidebar_state="collapsed")

from components import style  # noqa: E402  (set_page_config must run first)
from components.state import S, get_api_key, init_state, sync_url  # noqa: E402
from components.ui import nav_bar, scroll_to_top_on_view_change  # noqa: E402
from core import ai  # noqa: E402
from core.pricing import refresh_fx  # noqa: E402
from views.checkout import page_checkout, page_orders  # noqa: E402
from views.compare import page_compare  # noqa: E402
from views.home import page_home  # noqa: E402
from views.messages import page_chat, page_inbox  # noqa: E402
from views.product import page_detail  # noqa: E402
from views.profile import page_profile  # noqa: E402
from views.results import page_results  # noqa: E402

init_state()
if S.view == "paste":            # old address of Link paste
    S.view, S.tab = "home", "link"
if S.view == "orders" and not S.orders.get(S.order or ""):
    S.view = "profile"           # the order list lives in the profile
sync_url()
refresh_fx()                     # live ECB rates, at most every 6 h (15 min after a failure)
ai.set_api_key(get_api_key())
style.inject()
scroll_to_top_on_view_change()

PAGES = {"detail": page_detail, "compare": page_compare, "inbox": page_inbox, "chat": page_chat,
         "checkout": page_checkout, "orders": page_orders}

if S.view == "home":
    page_home()
elif S.view == "results":
    page_results()
elif S.view == "profile":        # draws its own band with the profile header
    page_profile()
else:
    nav_bar()
    PAGES.get(S.view, page_home)()
