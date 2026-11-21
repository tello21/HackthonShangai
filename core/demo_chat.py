"""Demo mode of the chat, used only while no API key is configured.

The five quick-action messages (Ask for quote, Ask for sample, ...) get a hand-written Chinese
translation with an English back-translation, and the simulated supplier answers with a scripted
reply built from the product's own listing data (price tier, MOQ, lead time). Any other text still
says "not available" without the AI. With an API key, core/messages.py uses the AI instead.
"""

import re

COUNTRY_ZH = {"Italy": "意大利", "France": "法国", "Germany": "德国", "Spain": "西班牙", "Portugal": "葡萄牙",
              "Netherlands": "荷兰", "Belgium": "比利时", "Austria": "奥地利", "Ireland": "爱尔兰",
              "Poland": "波兰", "Sweden": "瑞典", "Denmark": "丹麦", "Finland": "芬兰",
              "United Kingdom": "英国", "Switzerland": "瑞士", "Norway": "挪威", "Iceland": "冰岛",
              "United States": "美国"}

# tone -> (Chinese opening, Chinese closing, English opening, English closing)
TONE = {"polite": ("亲，您好！", "麻烦您了，谢谢！", "Hello! ", " Thank you very much!"),
        "neutral": ("您好，", "谢谢。", "Hello. ", " Thanks."),
        "firm": ("您好。", "", "Hello. ", "")}


def _item(context):
    en = (context.get("product_en") or "").lower()
    if "racket" in en or "padel" in en:
        return "板式网球拍", "支", "padel rackets"
    return "产品", "件", "items"


def translate(text_en, tone, context, quick_text):
    """Hand-written translation of a quick-action message, or None for any other text.
    quick_text(name) gives the English text of each quick action for this conversation."""
    item, unit, item_en = _item(context)
    qty = int(context.get("quantity") or 0)
    country = context.get("destination") or ""
    c_zh = COUNTRY_ZH.get(country, country)
    moq = int(context.get("listed_moq") or qty or 1)
    half = max(1, moq // 2)
    body = {
        "Ask for quote": (
            f"请问这款{item}订{qty}{unit}、发到{c_zh}的话，最优惠的单价是多少？请一并告知交期。",
            f"For an order of {qty:,} of these {item_en} delivered to {country}, what is your best unit "
            f"price? Please also tell me the lead time."),
        "Ask for sample": (
            f"下单{qty}{unit}之前，我想先拿一个样品看看。样品费是多少？寄到{c_zh}需要多长时间？",
            f"Before ordering {qty:,} units I would like to see a sample first. How much is the sample and "
            f"how long does it take to send it to {country}?"),
        "Customization": (
            "这款产品可以定制吗？我们需要印我们的logo、做定制颜色，并使用我们自己的包装。"
            "额外费用是多少？定制的起订量是多少？",
            "Can this product be customized? We need our logo printed, a custom colour and our own "
            "packaging. What is the extra cost, and what is the MOQ for customization?"),
        "Negotiate price": (
            f"谢谢您的报价。我们的目标价要低一些：{qty}{unit}的话，单价能再优惠一点吗？",
            f"Thank you for your quote. Our target price is lower: for {qty:,} units, can you give a "
            f"better unit price?"),
        "Negotiate MOQ": (
            f"你们的起订量是{moq}{unit}。第一次下单我们想先订{half}{unit}，可以吗？价格是多少？",
            f"Your MOQ is {moq:,} units. For a first order we would like {half:,} units. Is that "
            f"possible, and at what price?"),
    }
    for name, (zh, en) in body.items():
        if text_en.strip() == quick_text(name).strip():
            o_zh, c_zh_close, o_en, c_en = TONE.get(tone, TONE["neutral"])
            return {"zh": o_zh + zh + c_zh_close, "back_en": o_en + en + c_en}
    return None


def _offer(p):
    """A first offer a little under the listing price for the buyer's quantity, never under the floor."""
    floor, pct = p.get("floor_price_cny"), p.get("floor_pct") or 0.9
    if floor is None:
        return None
    listed = floor / pct
    return max(floor, round(listed * 0.95))


def supplier_reply(history, p):
    """Scripted reply in natural seller Chinese to the buyer's last message, or None."""
    last = next((m["zh"] for m in reversed(history) if m["role"] == "buyer"), "")
    qty = int(p.get("qty") or 500)
    unit = "支" if "球拍" in (p.get("product_zh") or "") or "padel" in (p.get("product_zh") or "").lower() else "件"
    moq, lead = p.get("moq") or 1, p.get("lead_time_days") or 15
    offer = _offer(p)
    if "最优惠的单价" in last and offer:
        return (f"亲，您好！{qty}{unit}的话单价可以给到¥{offer}，起订量{moq}{unit}，交期{lead}天左右。"
                f"付款方式是30%定金，发货前付清70%尾款。需要印logo吗？")
    if "目标价" in last and offer and p.get("floor_price_cny"):
        return (f"亲，这个价格已经很实在了。{qty}{unit}的话最低可以做到¥{p['floor_price_cny']:g}，"
                f"再低就亏本了。如果确认下单，我们可以优先安排生产。")
    if "样品" in last:
        return (f"可以的亲，样品费¥{p.get('sample_cost_cny')}，下单后可以退还。样品{p.get('sample_days', 5)}天左右发出，"
                f"寄到欧洲一般7到10天。")
    if "定制" in last:
        return (f"可以定制的亲。印logo每{unit}加¥5，定制颜色和包装起订量{max(moq, 100)}{unit}，"
                f"打样需要7天左右。")
    if "起订量是" in last:
        return f"亲，第一次合作可以的，按您说的数量下单，单价按{moq}{unit}的价格算。"
    return None


def analyze(text_zh):
    """English reading of a scripted supplier reply (same shape as the AI analysis), or None."""
    def num(pattern):
        m = re.search(pattern, text_zh)
        return m.group(1) if m else None

    blank = {"unit_price_cny": 0, "price_for_quantity": 0, "moq_units": 0, "lead_time": "", "payment_terms": "",
             "sample_cost": "", "shipping_terms": "", "customization": "", "seller_type": "", "certifications": ""}
    if "单价可以给到" in text_zh:
        qty, price, moq, lead = num(r"(\d+)[支件]的话"), num(r"¥([\d.]+)"), num(r"起订量(\d+)"), num(r"交期(\d+)天")
        terms = dict(blank, unit_price_cny=float(price), price_for_quantity=int(qty), moq_units=int(moq),
                     lead_time=f"about {lead} days", payment_terms="30% deposit, 70% before shipping")
        return {"en": f"Hello! For {int(qty):,} units the unit price can be ¥{price}, MOQ {moq} units, lead time "
                      f"about {lead} days. Payment is a 30% deposit and the 70% balance before shipping. "
                      f"Do you need a logo printed?",
                "meaning": "A standard first quote, slightly under the listing price: there is usually still "
                           "some room to negotiate. Asking about the logo is a way to keep the conversation going.",
                "highlights": [f"单价可以给到¥{price}", f"起订量{moq}", f"交期{lead}天左右", "30%定金", "70%尾款"],
                "terms": terms,
                "suggestions": [f"Can you do a better price for {int(qty):,} units?",
                                "Yes, a one-colour logo. What is the extra cost?",
                                "Can you send a sample first?"]}, None
    if "最低可以做到" in text_zh:
        qty, price = num(r"(\d+)[支件]的话"), num(r"¥([\d.]+)")
        return {"en": f"This price is already very fair. For {int(qty):,} units the lowest we can do is ¥{price}; "
                      f"any lower and we lose money. If you confirm the order we can prioritise production.",
                "meaning": "This is close to their floor price. Pushing further will probably not work; "
                           "ask for something else instead (free logo, faster delivery).",
                "highlights": [f"最低可以做到¥{price}"],
                "terms": dict(blank, unit_price_cny=float(price), price_for_quantity=int(qty)),
                "suggestions": ["OK, ¥" + price + " works if the logo printing is included.",
                                "Can you confirm the lead time for this order?"]}, None
    if "样品费" in text_zh:
        cost, days = num(r"样品费¥(\d+)"), num(r"样品(\d+)天")
        return {"en": f"Yes. The sample costs ¥{cost} and is refunded when you order. It ships in about {days} "
                      f"days; delivery to Europe usually takes 7 to 10 days.",
                "meaning": "A normal sample offer; a refundable sample fee is a good sign.",
                "highlights": [f"样品费¥{cost}", f"样品{days}天左右发出"],
                "terms": dict(blank, sample_cost=f"¥{cost}, refunded with the order"),
                "suggestions": ["Please send the sample. How do I pay the sample fee?"]}, None
    if "印logo每" in text_zh:
        moq = num(r"起订量(\d+)")
        return {"en": f"Yes, we can customize. Logo printing is ¥5 extra per unit; custom colour and packaging need "
                      f"a minimum of {moq} units, and a pre-production sample takes about 7 days.",
                "meaning": "Customization is possible with a higher MOQ: normal for a manufacturer.",
                "highlights": ["印logo每", f"起订量{moq}"],
                "terms": dict(blank, customization=f"logo +¥5/unit; colour and packaging from {moq} units",
                              moq_units=int(moq)),
                "suggestions": ["Please send a mock-up with our logo."]}, None
    if "第一次合作可以的" in text_zh:
        return {"en": "For a first order that is fine: order the quantity you asked for, at the MOQ unit price.",
                "meaning": "They accept a smaller first order without a price increase.",
                "highlights": ["第一次合作可以的"], "terms": blank,
                "suggestions": ["Great, please send the proforma invoice."]}, None
    return None
