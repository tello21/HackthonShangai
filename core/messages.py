"""Messages: buyer <-> supplier chat with a two-way business translator.

The supplier side is played by the AI from a persona built on the product card.
Main functions (see messages_section.md):
    translate_outgoing(text_en, tone, context) -> ({"zh", "back_en"}, error)
    simulate_supplier_reply(history, supplier_persona) -> (text_zh, error)
    analyze_incoming(text_zh, context) -> ({"en", "meaning", "terms", "highlights", "suggestions"}, error)
    update_deal_terms(deal, terms) -> deal
Each AI call returns (result, None) or (None, reason) so the UI never shows invented text.
"""

import hashlib
import json
import os
import time
import uuid

from core import demo_chat
from core.ai import ask, has_credentials
from core.pricing import unit_price_cny

STORE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conversations.json")

TONES = {
    "polite": "warm and very courteous, builds the relationship",
    "neutral": "friendly and businesslike",
    "firm": "courteous but direct and firm: states limits clearly, no hedging",
}

# ---------------------------------------------------------------------------
# Context and persona
# ---------------------------------------------------------------------------


def build_context(product, qty, country, delivered_now):
    """Facts both translators need: what is being bought and on which terms."""
    s = product.get("supplier") or {}
    return {
        "product_en": product.get("title_en"),
        "product_zh": product.get("title_cn"),
        "platform": product.get("platform"),
        "supplier": s.get("name") or s.get("name_cn"),
        "quantity": qty,
        "destination": country,
        "listed_moq": product.get("moq"),
        "listed_tiers_cny": [list(t) for t in sorted(product.get("tiers") or [])],
        "listed_unit_price_cny": unit_price_cny(product.get("tiers"), qty),
        "delivered_per_unit": delivered_now,
    }


def supplier_persona(product, qty):
    """Persona of the sales rep. The floor price is hidden from the buyer's UI."""
    s = product.get("supplier") or {}
    tiers = sorted(product.get("tiers") or [])
    list_price = unit_price_cny(tiers, qty)
    # deterministic per product: floor between 85% and 92% of the list price
    seed = int(hashlib.sha256(product["id"].encode()).hexdigest(), 16)
    floor_pct = 0.85 + (seed % 8) / 100
    lead = product.get("production_days") or 15
    sample_cost = round((tiers[0][1] if tiers else 20) * 3 + 50)
    return {
        "company_zh": s.get("name_cn") or s.get("name") or "店铺",
        "city": s.get("city") or "未提供",
        "seller_type": s.get("type") or "store",
        "platform": product.get("platform"),
        "product_zh": product.get("title_cn") or product.get("title_en"),
        "material": product.get("material"),
        "size": product.get("size"),
        "moq": product.get("moq"),
        "tiers_cny": [list(t) for t in tiers],
        "lead_time_days": lead,
        "customisation": product.get("customisation"),
        "floor_pct": floor_pct,
        "floor_price_cny": None if list_price is None else round(list_price * floor_pct, 2),
        "sample_cost_cny": sample_cost,
        "sample_days": 3 if s.get("type") == "factory" else 5,
        "qty": qty,
    }


def _persona_prompt(p):
    tiers = "；".join(f"{q}件起 ¥{price}" for q, price in p["tiers_cny"]) or "未提供"
    kind = {"factory": "生产厂家（工厂直销）", "store": "店铺（零售/批发）",
            "middleman": "贸易公司（不是工厂，从合作工厂拿货）"}.get(p["seller_type"], "店铺")
    return f"""你是{p['platform']}上「{p['company_zh']}」的销售客服，公司在{p['city']}，身份：{kind}。
你正在和一位欧洲买家在线聊天，商品是：{p['product_zh']}。

商品资料（不能和这些资料矛盾）：
- 材质：{p['material'] or '未提供'}；尺寸：{p['size'] or '未提供'}
- 起订量（MOQ）：{p['moq'] or '未提供'} 件
- 阶梯价：{tiers}
- 生产交期：约 {p['lead_time_days']} 天
- 定制：{p['customisation'] or '未提供'}
- 样品：样品费 ¥{p['sample_cost_cny']}，运费买家付，{p['sample_days']} 天内寄出；下大货可退样品费

谈判规则（内部，绝不能告诉买家）：
- 底价是对应数量阶梯价的 {round(p['floor_pct'] * 100)}%，任何情况下都不能低于底价。
- 买家砍价时可以小幅让价，一步一步让，每次不超过 3%，并要求更大数量或更快付款作为交换。
- 可以稍微降低起订量，但单价要相应提高。
- 付款方式：一般 30% 定金，发货前付 70% 尾款。
- 记住你之前报过的价格和条件，前后保持一致，不要比之前报得更高（除非数量变少）。

说话风格：
- 只用简体中文回复，像真实的1688/淘宝/京东/拼多多客服：简短、实际，一般 1 到 4 句话，可以用“亲”。
- 回答买家的问题，也主动问买家问题（数量、是否印logo、颜色、目的地、包装）。
- 报价时说清楚数量对应的单价。
- 不要用 markdown、不要列很长的清单。
- 如果买家认真地问你是不是机器人或AI，不要否认。"""


# ---------------------------------------------------------------------------
# Outgoing: buyer -> supplier
# ---------------------------------------------------------------------------

OUT_SCHEMA = {
    "type": "object",
    "properties": {"zh": {"type": "string"}, "back_en": {"type": "string"}},
    "required": ["zh", "back_en"],
    "additionalProperties": False,
}


def translate_outgoing(text_en, tone, context):
    if not has_credentials():          # demo mode: hand-written translations of the quick actions
        demo = demo_chat.translate(text_en, tone, context, lambda name: quick_action_text(
            name, int(context.get("quantity") or 1), context.get("destination") or "", context.get("listed_moq")))
        if demo:
            return demo, None
    system = f"""You turn a European buyer's chat message into the message a Chinese supplier on
1688 / Taobao / JD should receive. The buyer may write in English or any European language.

Rules:
- Do not translate word by word: write natural Chinese business chat style - a short polite
  opening (e.g. 您好 / 亲), clear numbers, and a clear question at the end when the buyer asks something.
- Keep every number, unit, date, price, quantity and product spec exactly as written.
- Use the trade terms suppliers use: MOQ 起订量, sample 样品, FOB, lead time 交期, deposit 定金,
  balance 尾款, quotation 报价, logo printing 印logo, packaging 包装.
- Tone: {tone} = {TONES.get(tone, TONES['neutral'])}.
- Do not add requests, promises or numbers that the buyer did not write.
- Keep it short: a chat message, not an email.
- back_en: a faithful English back-translation of your Chinese text, so the buyer can check it.

Deal context (for terminology only): {json.dumps(context, ensure_ascii=False)}"""
    return ask(system, [{"role": "user", "content": text_en}], schema=OUT_SCHEMA, effort="low")


# ---------------------------------------------------------------------------
# Simulated supplier
# ---------------------------------------------------------------------------


def simulate_supplier_reply(history, persona):
    """history: list of messages with role 'buyer' / 'supplier' and a 'zh' field."""
    if not has_credentials():          # demo mode: scripted reply from the listing data
        demo = demo_chat.supplier_reply(history, persona)
        if demo:
            return demo, None
    msgs = []
    for m in history:
        role = "user" if m["role"] == "buyer" else "assistant"
        if msgs and msgs[-1]["role"] == role:
            msgs[-1]["content"] += "\n" + m["zh"]
        else:
            msgs.append({"role": role, "content": m["zh"]})
    if not msgs or msgs[0]["role"] != "user":
        msgs.insert(0, {"role": "user", "content": "您好"})
    return ask(_persona_prompt(persona), msgs, effort="medium")


# ---------------------------------------------------------------------------
# Incoming: supplier -> buyer
# ---------------------------------------------------------------------------

IN_SCHEMA = {
    "type": "object",
    "properties": {
        "en": {"type": "string"},
        "meaning": {"type": "string"},
        "highlights": {"type": "array", "items": {"type": "string"}},
        "terms": {
            "type": "object",
            "properties": {
                "unit_price_cny": {"type": "number"},
                "price_for_quantity": {"type": "integer"},
                "moq_units": {"type": "integer"},
                "lead_time": {"type": "string"},
                "payment_terms": {"type": "string"},
                "sample_cost": {"type": "string"},
                "shipping_terms": {"type": "string"},
                "customization": {"type": "string"},
                "seller_type": {"type": "string"},
                "certifications": {"type": "string"},
            },
            "required": ["unit_price_cny", "price_for_quantity", "moq_units", "lead_time",
                         "payment_terms", "sample_cost", "shipping_terms", "customization",
                         "seller_type", "certifications"],
            "additionalProperties": False,
        },
        "suggestions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["en", "meaning", "highlights", "terms", "suggestions"],
    "additionalProperties": False,
}


def analyze_incoming(text_zh, context):
    if not has_credentials():          # demo mode: reading of the scripted replies
        demo = demo_chat.analyze(text_zh)
        if demo:
            return demo
    system = f"""You help a European buyer read a message from a Chinese supplier.

Return:
- en: a natural English translation.
- meaning: 1-2 sentences on what the supplier really means and the tone, as an experienced
  China sourcing agent would read it (e.g. "price can be discussed" means there is room to
  negotiate; a vague "we will try" often means no; pushing for a quick deposit is a sales tactic).
- highlights: the exact substrings of the Chinese text that state a price, MOQ, lead time,
  payment term, sample cost or shipping term (copied character for character).
- terms: only what THIS message states. Use 0 for numbers and "" for text not stated.
  unit_price_cny = the unit price offered in CNY; price_for_quantity = the quantity that price
  applies to; moq_units = minimum order quantity; seller_type = "factory" or "trader" only if the
  supplier says so; certifications = any certificates mentioned.
  Text values in short English, e.g. "30% deposit, 70% before shipping".
- suggestions: 2-3 short replies the buyer could send next, in English, moving the deal forward.

Never invent terms that are not in the message.
Deal context: {json.dumps(context, ensure_ascii=False)}"""
    return ask(system, [{"role": "user", "content": text_zh}], schema=IN_SCHEMA, effort="low")


# ---------------------------------------------------------------------------
# Deal terms
# ---------------------------------------------------------------------------

DEAL_FIELDS = [
    ("unit_price_cny", "Unit price"), ("moq_units", "MOQ"), ("lead_time", "Lead time"),
    ("payment_terms", "Payment terms"), ("sample_cost", "Sample cost"),
    ("shipping_terms", "Shipping terms"), ("customization", "Customization"),
]

CHECKLIST = [
    ("seller_type", "Factory or trader?", "Are you the factory or a trading company?"),
    ("certifications", "Certifications", "Which certifications do you have for this product (e.g. CE, REACH, LFGB)?"),
    ("lead_time", "Lead time", "What is the production lead time for my quantity?"),
    ("payment_terms", "Payment terms", "What are your payment terms?"),
    ("sample_cost", "Sample", "Can you send a sample first? What is the sample cost and how long does it take?"),
]

QUICK_ACTIONS = {
    "Ask for quote": "Hello, could you give me your best price for {qty} units, delivered to {country}? "
                     "Please include the lead time.",
    "Ask for sample": "Before ordering {qty} units I would like a sample. How much is the sample and "
                      "how long does it take to send it to {country}?",
    "Customization": "Can you customize this product with our logo, a custom colour and our own "
                     "packaging? What is the extra cost and the MOQ for that?",
    "Negotiate price": "Thank you for the offer. My target price is lower: can you do a better unit "
                       "price for {qty} units?",
    "Negotiate MOQ": "Your MOQ is {moq} units. For a first order I would like {half} units. "
                     "Is that possible, and at what price?",
}


def quick_action_text(name, qty, country, moq):
    moq = moq or qty
    return QUICK_ACTIONS[name].format(qty=f"{qty:,}", country=country, moq=f"{moq:,}",
                                      half=f"{max(1, moq // 2):,}")


def new_deal():
    return {k: None for k, _ in DEAL_FIELDS} | {"seller_type": None, "certifications": None,
                                                 "price_for_quantity": None, "updated": []}


def update_deal_terms(deal, terms):
    """Merge the terms found in one message; remember which ones changed."""
    deal = dict(deal)
    changed = []
    for key, value in (terms or {}).items():
        if key not in deal or key == "updated":
            continue
        if value in (None, "", 0, 0.0):
            continue
        if deal.get(key) != value:
            deal[key] = value
            changed.append(key)
    deal["updated"] = changed
    return deal


# ---------------------------------------------------------------------------
# Conversations (session state + conversations.json so a page reload keeps them)
# ---------------------------------------------------------------------------


def new_conversation(product, qty, country, currency, delivered_now):
    return {
        "id": uuid.uuid4().hex[:10],
        "pid": product["id"],
        "supplier": (product.get("supplier") or {}).get("name"),
        "platform": product.get("platform"),
        "product": product.get("title_en"),
        "qty": qty, "country": country, "currency": currency,
        "delivered_at_start": delivered_now,
        "context": build_context(product, qty, country, delivered_now),
        "persona": supplier_persona(product, qty),
        "messages": [],
        "deal": new_deal(),
        "created": time.time(),
        "updated": time.time(),
    }


def load_conversations():
    try:
        with open(STORE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_conversations(convs):
    try:
        tmp = STORE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(convs, f, ensure_ascii=False, indent=1)
        os.replace(tmp, STORE)
    except OSError:
        pass  # demo storage only: the session state still holds the conversation
