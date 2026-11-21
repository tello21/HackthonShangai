"""Messages: inbox and chat with the supplier (two-way translator + deal panel)."""

import json
import random
import re
import time

import streamlit as st

from components import style
from components.state import S, link
from components.ui import NA, esc, money, platform_tag, receipt
from core import messages as M
from core.pricing import SYMBOL, delivered, fx_rate
from views.product import start_checkout


def ago(ts):
    s = max(0, time.time() - ts)
    if s < 60:
        return "now"
    if s < 3600:
        return f"{int(s // 60)} min"
    if s < 86400:
        return time.strftime("%H:%M", time.localtime(ts))
    return time.strftime("%d %b", time.localtime(ts))


# ---------------------------------------------------------------------------- inbox
def render_inbox():
    convs = sorted(S.convs.values(), key=lambda c: c["updated"], reverse=True)
    if not convs:
        st.info("No conversations yet. Open a product and tap “Contact supplier”.")
        return
    rows = []
    for c in convs:
        last = c["messages"][-1] if c["messages"] else None
        if last is None:
            preview = "<span class='na'>No messages yet — your draft is ready</span>"
        elif last["role"] == "buyer":
            preview = "You: " + esc(last.get("en") or "")
        else:
            preview = esc((last.get("analysis") or {}).get("en") or last["zh"])
        unread = any(m["role"] == "supplier" and not m.get("read") for m in c["messages"])
        rows.append(
            f"<a class='ib{' unread' if unread else ''}' href='{link(view='chat', conv=c['id'])}' target='_self'>"
            f"<span class='ib-top'><span class='ib-name'>{esc(c['supplier'] or NA)}</span>"
            f"<span class='ib-time'>{ago(c['updated'])}</span></span>"
            f"<span class='ib-prod'>{platform_tag(c['platform'])} {esc(c['product'] or NA)}</span>"
            f"<span class='ib-last'>{preview}</span></a>")
    st.markdown("".join(rows), unsafe_allow_html=True)


def page_inbox():
    st.header("Messages")
    render_inbox()


# ---------------------------------------------------------------------------- AI calls (cached; failures never cached)
class _AIUnavailable(Exception):
    pass


@st.cache_data(show_spinner=False, max_entries=2000)
def _translate_cached(text, tone, context_json):
    out, err = M.translate_outgoing(text, tone, json.loads(context_json))
    if out is None:
        raise _AIUnavailable(err)
    return out


@st.cache_data(show_spinner=False, max_entries=2000)
def _analyze_cached(text_zh, context_json):
    out, err = M.analyze_incoming(text_zh, json.loads(context_json))
    if out is None:
        raise _AIUnavailable(err)
    return out


# ---------------------------------------------------------------------------- bubbles
def highlight_zh(text, highlights):
    """Escape the supplier text and mark the key-term substrings the analysis found."""
    out = esc(text)
    parts = sorted({esc(h) for h in highlights or [] if h and h in text}, key=len, reverse=True)
    if parts:
        out = re.sub("|".join(re.escape(p) for p in parts), lambda m: f"<mark>{m.group(0)}</mark>", out)
    return out.replace("\n", "<br>")


TERM_LABELS = {"unit_price_cny": "Price", "moq_units": "MOQ", "lead_time": "Lead time",
               "payment_terms": "Payment", "sample_cost": "Sample", "shipping_terms": "Shipping",
               "customization": "Customization", "seller_type": "Seller", "certifications": "Certificates"}


def term_chips(terms):
    chips = []
    for k, label in TERM_LABELS.items():
        v = (terms or {}).get(k)
        if v in (None, "", 0, 0.0):
            continue
        if k == "unit_price_cny":
            q = terms.get("price_for_quantity")
            v = f"¥{v:g}" + (f" @ {q:,} pcs" if q else "")
        elif k == "moq_units":
            v = f"{v:,} pcs"
        chips.append(f"<span class='term'>{label}: {esc(v)}</span>")
    return f"<div class='terms'>{''.join(chips)}</div>" if chips else ""


def bubble(m):
    t = ago(m["ts"])
    if m["role"] == "buyer":
        return (f"<div class='b me'>{esc(m['zh']).replace(chr(10), '<br>')}"
                f"<div class='b-sub'>You wrote: {esc(m.get('en') or '')} · {t}</div></div>")
    a = m.get("analysis")
    if not a:
        return (f"<div class='b them'>{esc(m['zh']).replace(chr(10), '<br>')}"
                f"<div class='b-sub'>Translation not available — {esc(m.get('analysis_error') or '')} · {t}</div></div>")
    return (f"<div class='b them'>{highlight_zh(m['zh'], a.get('highlights'))}"
            f"<div class='b-en'>{esc(a['en'])}</div>"
            f"<div class='mean'><b>What they mean:</b> {esc(a['meaning'])}</div>"
            f"{term_chips(a.get('terms'))}<div class='b-sub'>{t}</div></div>")


# ---------------------------------------------------------------------------- callbacks
def _set_draft(conv_id, text):
    S[f"draft_{conv_id}"] = text


def _quick_action(conv):
    key = f"qa_{conv['id']}"
    name = S.get(key)
    if name:
        S[f"draft_{conv['id']}"] = M.quick_action_text(name, conv["qty"], conv["country"],
                                                       conv["context"].get("listed_moq"))
        S[key] = None  # pills act as one-shot buttons


def _preview(conv):
    cid = conv["id"]
    text = (S.get(f"draft_{cid}") or "").strip()
    tone = S.get(f"tone_{cid}") or "polite"
    if not text:
        S[f"prev_{cid}"] = {"error": "Write a message first."}
        return
    try:
        out = _translate_cached(text, tone, json.dumps(conv["context"], ensure_ascii=False, sort_keys=True))
        S[f"prev_{cid}"] = {"src": text, "tone": tone, **out}
    except _AIUnavailable as e:
        S[f"prev_{cid}"] = {"error": f"Translation not available — {e}"}


def _send(conv):
    cid = conv["id"]
    prev = S.get(f"prev_{cid}") or {}
    conv["messages"].append({"role": "buyer", "en": prev["src"], "zh": prev["zh"],
                             "back_en": prev["back_en"], "tone": prev["tone"], "ts": time.time()})
    conv["updated"] = time.time()
    conv["pending"] = True
    S[f"draft_{cid}"] = ""
    S[f"prev_{cid}"] = None
    M.save_conversations(S.convs)


def _negotiated_qty(conv):
    return max(conv["qty"], conv["deal"].get("price_for_quantity") or 0)


def _recalc(conv):
    """Delivered price with the negotiated unit price (and MOQ) instead of the listing's."""
    deal, card = conv["deal"], conv["card"]
    new_card = dict(card, tiers=[[1, deal["unit_price_cny"]]])
    if deal.get("moq_units"):
        new_card["moq"] = deal["moq_units"]
    qty = _negotiated_qty(conv)
    before = delivered(card, qty, conv["country"], S.cur)
    after = delivered(new_card, qty, conv["country"], S.cur)
    conv["recalc"] = {"qty": qty, "cur": S.cur, "before": before["per_unit"], "after": after["per_unit"],
                      "before_total": before["total"], "after_total": after["total"],
                      "mode": after["mode_label"], "days": after["transit_days"], "ts": time.time()}
    M.save_conversations(S.convs)


def _order_negotiated(conv):
    card = dict(conv["card"])
    if conv["deal"].get("moq_units"):
        card["moq"] = conv["deal"]["moq_units"]
    start_checkout(card, _negotiated_qty(conv), conv["country"], "auto",
                   unit_price_cny=conv["deal"]["unit_price_cny"], conv_id=conv["id"])


# ---------------------------------------------------------------------------- deal panel
def deal_panel(conv):
    deal, ctx, sym = conv["deal"], conv["context"], SYMBOL[S.cur]
    listing = {
        "unit_price_cny": f"¥{ctx['listed_unit_price_cny']:g}" if ctx.get("listed_unit_price_cny") else None,
        "moq_units": f"{ctx['listed_moq']:,} pcs" if ctx.get("listed_moq") else None,
        "lead_time": f"{conv['card'].get('production_days')} days" if conv["card"].get("production_days") else None,
        "customization": conv["card"].get("customisation"),
    }
    rows = []
    for k, label in M.DEAL_FIELDS:
        v = deal.get(k)
        if v not in (None, "", 0):
            if k == "unit_price_cny":
                q = deal.get("price_for_quantity")
                v = f"¥{v:g}" + (f" @ {q:,} pcs" if q else "")
            elif k == "moq_units":
                v = f"{v:,} pcs"
            cell = f"{esc(v)}<span class='src'>from chat</span>"
            cls = " new" if k in deal.get("updated", []) else ""
        elif listing.get(k):
            cell, cls = f"{esc(listing[k])}<span class='src'>listing</span>", ""
        else:
            cell, cls = "<span class='na'>not discussed yet</span>", ""
        rows.append(f"<div class='deal-row{cls}'><span>{label}</span><span class='v'>{cell}</span></div>")
    st.markdown("**Deal terms**" + "".join(rows), unsafe_allow_html=True)

    can = bool(deal.get("unit_price_cny"))
    st.button("Recalculate delivered price", key=f"recalc_{conv['id']}", disabled=not can,
              on_click=_recalc, args=(conv,), width="stretch",
              help=None if can else "Available once the supplier quotes a unit price")
    r = conv.get("recalc")
    if r and r["cur"] == S.cur:
        diff = "" if not (r["before"] and r["after"]) else f" ({(r['after'] - r['before']) / r['before'] * 100:+.1f}%)"
        st.markdown(receipt([("Listing price", r["before_total"], f"delivered, {r['qty']:,} units")],
                            "Negotiated", f"{r['mode']}, {r['days']} days{diff}",
                            r["after_total"], r["after"], r["qty"], sym), unsafe_allow_html=True)
        st.button("🛒 Order at negotiated price", key=f"order_neg_{conv['id']}", type="primary",
                  on_click=_order_negotiated, args=(conv,), width="stretch",
                  disabled=r["after"] is None)

    st.markdown("**Still to ask**")
    for k, label, question in M.CHECKLIST:
        if deal.get(k) not in (None, "", 0):
            st.markdown(f"✅ {label}")
        else:
            st.button(f"☐ {label} — ask", key=f"ask_{k}_{conv['id']}", on_click=_set_draft,
                      args=(conv["id"], question), type="tertiary")


# ---------------------------------------------------------------------------- chat
def _receive_reply(conv):
    """Ask the simulated supplier, analyse the reply, update the deal (1-3 s 'typing…')."""
    st.markdown("<div class='chat'><div class='typing'>typing…</div></div>", unsafe_allow_html=True)
    start = time.time()
    reply, err = M.simulate_supplier_reply(conv["messages"], conv["persona"])
    if reply is None:
        conv["pending"] = False
        conv["error"] = f"Message delivered, but the reply could not be loaded — {err}"
        M.save_conversations(S.convs)
        st.rerun()
    ctx = dict(conv["context"], current_deal={k: v for k, v in conv["deal"].items() if k != "updated"})
    try:
        analysis, a_err = _analyze_cached(reply, json.dumps(ctx, ensure_ascii=False, sort_keys=True)), None
    except _AIUnavailable as e:
        analysis, a_err = None, str(e)
    wait = random.uniform(1, 3) - (time.time() - start)
    if wait > 0:
        time.sleep(wait)
    conv["messages"].append({"role": "supplier", "zh": reply, "analysis": analysis,
                             "analysis_error": a_err, "ts": time.time(), "read": True})
    if analysis:
        conv["deal"] = M.update_deal_terms(conv["deal"], analysis.get("terms"))
    conv.update(pending=False, error=None, updated=time.time())
    M.save_conversations(S.convs)
    st.rerun()


def composer(conv):
    cid = conv["id"]
    last = conv["messages"][-1] if conv["messages"] else None
    if last and last["role"] == "supplier" and last.get("analysis"):
        sugg = last["analysis"].get("suggestions") or []
        if sugg:
            st.caption("Suggested replies — tap to use as a draft")
            for i, s_ in enumerate(sugg[:3]):
                st.button(s_, key=f"sugg_{cid}_{len(conv['messages'])}_{i}", on_click=_set_draft,
                          args=(cid, s_), width="stretch")

    st.pills("Quick actions", list(M.QUICK_ACTIONS), key=f"qa_{cid}", on_change=_quick_action,
             args=(conv,), label_visibility="collapsed")
    st.text_area("Your message", key=f"draft_{cid}", height=110,
                 placeholder="Write in English or any language…", label_visibility="collapsed")
    tone_key = f"tone_{cid}"
    S.setdefault(tone_key, "polite")
    st.segmented_control("Tone", ["polite", "neutral", "firm"], key=tone_key, format_func=str.capitalize)

    prev = S.get(f"prev_{cid}")
    draft_now = (S.get(f"draft_{cid}") or "").strip()
    fresh = bool(prev and not prev.get("error") and prev.get("src") == draft_now
                 and prev.get("tone") == S.get(tone_key))
    if prev and prev.get("error"):
        st.warning(prev["error"])
    elif fresh:
        st.markdown(f"<div class='preview'><b>Will be sent:</b><br>{esc(prev['zh']).replace(chr(10), '<br>')}"
                    f"<div class='bt'>Means: {esc(prev['back_en'])}</div></div>", unsafe_allow_html=True)
    b1, b2 = st.columns([1.3, 1])
    with b1:
        st.markdown("<span class='nowrap'></span>", unsafe_allow_html=True)
        st.button("Preview in Chinese", key=f"pv_{cid}", on_click=_preview, args=(conv,),
                  width="stretch", disabled=not draft_now)
    with b2:
        st.button("Send", key=f"send_{cid}", type="primary", on_click=_send, args=(conv,),
                  width="stretch", disabled=not fresh or bool(conv.get("pending")))
    if draft_now and not fresh:
        st.caption("Preview the Chinese version first, then send.")


def page_chat():
    style.wide()
    conv = S.convs.get(S.conv)
    if not conv:
        st.warning("Conversation not found.")
        st.markdown(f"<a href='{link(view='inbox')}' target='_self'>← All messages</a>", unsafe_allow_html=True)
        return

    # opening the chat marks supplier messages as read
    if any(m["role"] == "supplier" and not m.get("read") for m in conv["messages"]):
        for m in conv["messages"]:
            m["read"] = True
        M.save_conversations(S.convs)

    listed = ""
    if conv.get("delivered_at_start"):
        v = conv["delivered_at_start"] * fx_rate(S.cur) / fx_rate(conv["currency"])
        listed = f" · listed delivered price {money(v, SYMBOL[S.cur])}/unit"
    st.markdown(
        f"<div class='chat-head'><a class='rh-back' href='{link(view='inbox')}' target='_self'>← All messages</a>"
        f"<div class='who'>{esc(conv['supplier'] or NA)}</div>"
        f"<div class='muted'>{platform_tag(conv['platform'])} {esc(conv['product'] or NA)} · "
        f"{conv['qty']:,} units to {esc(conv['country'])}{listed}</div></div>", unsafe_allow_html=True)

    c_chat, c_deal = st.columns([1.75, 1], gap="large")
    with c_chat:
        st.markdown("<div class='chat'>" + "".join(bubble(m) for m in conv["messages"]) + "</div>",
                    unsafe_allow_html=True)
        if conv.get("pending"):
            _receive_reply(conv)
        if conv.get("error"):
            st.warning(conv["error"])
        composer(conv)
    with c_deal:
        with st.container(border=True):
            deal_panel(conv)
