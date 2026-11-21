"""Side-by-side comparison of 2-3 products."""

import pandas as pd
import streamlit as st

from components.state import S, go, link
from components.ui import NA, cny, money, sample_banner
from views.live import find_product
from core.pricing import delivered
from core.supplier_score import trust_for


def page_compare():
    st.button("← Back to results", on_click=go, args=("results",))
    st.header("Compare")
    sample_banner()
    prods = [p for p in (find_product(pid) for pid in S.cmp) if p]
    if len(prods) < 2:
        st.info("Pick 2 or 3 products under “Compare products” on the results page.")
        return
    st.markdown(f"<span class='muted'>{S.qty:,} units delivered to {S.country} · {S.cur}</span>",
                unsafe_allow_html=True)
    data = {}
    for p in prods:
        d = delivered(p, S.qty, S.country, S.cur)
        tr = (S.get("trust") or {}).get(p["id"]) or trust_for(p, d["unit_cny"])
        title = (p.get("title_en") or p.get("title_cn") or NA)[:30]
        data[f"{p['platform']} · {title}…"] = {
            "Delivered / unit (est.)": money(d["per_unit"], d["symbol"]),
            "Total delivered (est.)": money(d["total"], d["symbol"]),
            "Seller price / unit": cny(d["unit_cny"]),
            "Shipping": f"{d['mode_label']} · {d['transit_days']} days" if d["mode"] else NA,
            "MOQ": f"{p['moq']:,}" if p["moq"] is not None else NA,
            "Lead time": f"{p['production_days']} days" if p["production_days"] is not None else NA,
            "Trust score": f"{tr['score']}/100 ({tr['band']})" if tr["score"] is not None else tr["band"],
            "Trust — top signals": " · ".join(tr["reasons"][:2]) or NA,
            "Seller type": (p["supplier"].get("type") or NA).capitalize(),
        }
    st.dataframe(pd.DataFrame(data), width="stretch")
    st.markdown(" · ".join(f"<a href='{link(view='detail', pid=p['id'])}' target='_self'>"
                           f"{p['platform']} details →</a>" for p in prods), unsafe_allow_html=True)
