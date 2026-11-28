"""Demo mode of the chat, used only while no API key is configured.

Instead of an exact sentence, the buyer's message (English, or Italian for the common words) is read
topic by topic: price, lead time, sample, logo, packaging, colour, MOQ, shipping, payment,
certificates, factory or trader, stock, specs. Each topic found becomes a prepared sentence of
natural seller Chinese, filled with the numbers of the message (quantity, target price, days, MOQ)
or of the conversation, with a faithful English back-translation. Works for every product.

The simulated supplier answers each topic of the buyer's last message from the listing data
(price tier for the quantity, MOQ, lead time, customisation, seller type); what the listing doesn't
say (e.g. certificates) is answered as "to be checked", never invented. With an API key,
core/messages.py uses the AI instead.
"""

import re

COUNTRY_ZH = {"Italy": "意大利", "France": "法国", "Germany": "德国", "Spain": "西班牙", "Portugal": "葡萄牙",
              "Netherlands": "荷兰", "Belgium": "比利时", "Austria": "奥地利", "Ireland": "爱尔兰",
              "Poland": "波兰", "Sweden": "瑞典", "Denmark": "丹麦", "Finland": "芬兰",
              "United Kingdom": "英国", "Switzerland": "瑞士", "Norway": "挪威", "Iceland": "冰岛",
              "United States": "美国"}
COUNTRY_WORDS = {"italy": "Italy", "italia": "Italy", "france": "France", "germany": "Germany",
                 "spain": "Spain", "portugal": "Portugal", "netherlands": "Netherlands", "belgium": "Belgium",
                 "austria": "Austria", "ireland": "Ireland", "poland": "Poland", "sweden": "Sweden",
                 "denmark": "Denmark", "finland": "Finland", "uk": "United Kingdom",
                 "united kingdom": "United Kingdom", "switzerland": "Switzerland", "norway": "Norway",
                 "iceland": "Iceland", "usa": "United States", "united states": "United States"}

# tone -> (Chinese opening, Chinese closing, English opening, English closing)
TONE = {"polite": ("亲，您好！", "麻烦您了，谢谢！", "Hello! ", " Thank you very much!"),
        "neutral": ("您好，", "谢谢。", "Hello. ", " Thanks."),
        "firm": ("您好。", "", "Hello. ", "")}

# topic -> words that reveal it in the buyer's message (English + common Italian)
TOPICS = [
    ("nego", r"target price|better (unit )?price|lower price|cheaper|discount|best you can do|can you do|"
             r"too (high|expensive)|prezzo migliore|sconto|troppo caro"),
    ("quote", r"price|quote|quotation|cost per|unit cost|prezzo|preventivo|quanto costa|quanto viene"),
    ("moq", r"\bmoq\b|minimum order|minimum quantity|smaller (order|quantity)|first order|ordine minimo|"
            r"quantit[aà] minima|primo ordine"),
    ("lead", r"lead time|delivery time|production time|how many days|when can you (ship|deliver)|"
             r"within \d+ days|tempi di consegna|consegna in"),
    ("sample", r"sample|campion"),
    ("logo", r"logo|oem|private label|our brand|custom(i[sz]e|i[sz]ation)?\b|personalizz"),
    ("packaging", r"packag|box|confezion|imballo"),
    ("colour", r"colou?r|colore"),
    ("shipping", r"ship|freight|\bsea\b|\bair\b|express|courier|\bddp\b|\bfob\b|spedizion|spedire"),
    ("payment", r"payment|pay\b|deposit|paypal|bank transfer|letter of credit|pagamento|acconto"),
    ("cert", r"certif|\bce\b|reach|rohs|test report|certificat"),
    ("factory", r"factory|manufacturer|trading company|trader|fabbrica|produttore"),
    ("stock", r"in stock|stock|ready to ship|available now|disponibil|magazzino"),
    ("specs", r"weight|grams|\bspec|material|thickness|balance|peso|materiale|spessore"),
]
GREETING = r"^\s*(hello|hi|hey|dear|good (morning|afternoon)|ciao|buongiorno|salve)\b"


def _item(context):
    en = (context.get("product_en") or "").lower()
    if "racket" in en or "padel" in en:
        return "板式网球拍", "支", "padel rackets"
    return "产品", "件", "items"


def _num(s):
    return float(s.replace(",", ""))


def _facts(text, context):
    """Numbers and choices written in the message; the conversation fills what is missing."""
    t = text.lower()
    # the order quantity: "for 500 units", "order 300 pcs"... (not "MOQ is 2 units"); else the conversation's
    m = re.search(r"(?:for|order(?:ing)?(?: of)?|need|buy|per|di)\s+(\d[\d,]*)\s*(?:units?|pcs|pieces|rackets?|"
                  r"racquets?|paddles?|pezzi|racchette|unit[aà])", t)
    qty = int(_num(m.group(1))) if m else int(context.get("quantity") or 0)
    country = next((c for w, c in COUNTRY_WORDS.items() if re.search(r"\b" + w + r"\b", t)),
                   context.get("destination") or "")
    price, cur = None, None
    m = (re.search(r"(¥|cny|rmb|€|eur|\$|usd)\s*(\d+(?:[.,]\d+)?)", t)
         or re.search(r"(\d+(?:[.,]\d+)?)\s*(¥|cny|rmb|yuan|€|eur|euros?|\$|usd|dollars?)", t))
    if m:
        a, b = m.groups()
        num, sym = (b, a) if a[0] in "¥€$cerud" and not a[0].isdigit() else (a, b)
        price = float(num.replace(",", "."))
        cur = "CNY" if sym[0] in "¥cry" else ("EUR" if sym[0] in "€e" else "USD")
    m = (re.search(r"(?:first order|start with|only|solo|primo ordine)\D{0,20}(\d[\d,]*)", t)
         or re.search(r"(?:minimum of|moq of)\D{0,5}(\d[\d,]*)", t))
    moq_ask = int(_num(m.group(1))) if m else None
    m = re.search(r"(?:within|in|entro|in)\s*(\d+)\s*(?:days|giorni)", t)
    days = int(m.group(1)) if m else None
    mode = next((zh for w, zh in [("sea", "海运"), ("air", "空运"), ("rail", "铁路"), ("train", "铁路"),
                                  ("express", "快递"), ("courier", "快递"), ("ddp", "DDP")] if re.search(r"\b" + w, t)),
                None)
    return dict(qty=qty, country=country, price=price, cur=cur, moq_ask=moq_ask, days=days, mode=mode)


STRONG_QUOTE = r"price|quote|quotation|prezzo|preventivo"


def topics_of(text):
    """The topics of a message, in the order they are written."""
    t = text.lower()
    hits = []
    for name, pattern in TOPICS:
        m = re.search(pattern, t)
        if m:
            hits.append((m.start(), name))
    found = [name for _, name in sorted(hits)]
    if "nego" in found and "quote" in found:
        found.remove("quote")                      # "better price" is a negotiation, not a first quote
    if "sample" in found and "quote" in found and not re.search(STRONG_QUOTE, t):
        found.remove("quote")                      # "how much is the sample" asks the sample cost
    return found


def _sentences(topic, f, context):
    """(Chinese, English) for one topic of the buyer's message."""
    item, unit, item_en = _item(context)
    qty, country = f["qty"], f["country"]
    c_zh = COUNTRY_ZH.get(country, country)
    if topic == "quote":
        where_zh, where_en = (f"、发到{c_zh}", f" delivered to {country}") if country else ("", "")
        return (f"请问这款{item}订{qty}{unit}{where_zh}的话，最优惠的单价是多少？",
                f"For an order of {qty:,} of these {item_en}{where_en}, what is your best unit price?")
    if topic == "nego":
        if f["price"] is not None:
            sym = {"CNY": "¥", "EUR": "€", "USD": "$"}[f["cur"]]
            return (f"{qty}{unit}的话，单价{sym}{f['price']:g}可以吗？",
                    f"For {qty:,} units, could you do {sym}{f['price']:g} per unit?")
        return (f"谢谢您的报价。我们的目标价要低一些：{qty}{unit}的话，单价能再优惠一点吗？",
                f"Thank you for your quote. Our target price is lower: for {qty:,} units, can you give a better "
                f"unit price?")
    if topic == "moq":
        if f["moq_ask"]:
            return (f"第一次下单我们想先订{f['moq_ask']}{unit}，可以吗？价格是多少？",
                    f"For a first order we would like {f['moq_ask']:,} units. Is that possible, and at what price?")
        return ("请问起订量是多少？", "What is your minimum order quantity?")
    if topic == "lead":
        if f["days"]:
            return (f"能在{f['days']}天内交货吗？", f"Can you deliver within {f['days']} days?")
        return ("请一并告知交期。", "Please also tell me the lead time.")
    if topic == "sample":
        where = f"寄到{c_zh}" if country else "寄过来"
        return (f"下单之前我想先拿一个样品看看。样品费是多少？{where}需要多长时间？",
                f"Before ordering I would like a sample first. How much is the sample and how long does it take "
                f"to send it{' to ' + country if country else ''}?")
    if topic == "logo":
        return ("可以印我们的logo吗？额外费用是多少？", "Can you print our logo? What is the extra cost?")
    if topic == "packaging":
        return ("可以用我们自己的包装吗？", "Can you use our own packaging?")
    if topic == "colour":
        return ("颜色可以定制吗？", "Can the colour be customised?")
    if topic == "shipping":
        how = f"用{f['mode']}" if f["mode"] else ""
        how_en = {"海运": " by sea", "空运": " by air", "铁路": " by rail", "快递": " by express courier",
                  "DDP": " DDP"}.get(f["mode"], "")
        return (f"可以{how}发到{c_zh}吗？运费大概多少？" if country else f"可以{how}发货吗？运费大概多少？",
                f"Can you ship{how_en}{' to ' + country if country else ''}? Roughly how much is the freight?")
    if topic == "payment":
        return ("请问付款方式是怎样的？", "What are your payment terms?")
    if topic == "cert":
        return ("这款产品有CE、REACH等认证或检测报告吗？",
                "Does this product have certificates or test reports, such as CE or REACH?")
    if topic == "factory":
        return ("请问你们是工厂还是贸易公司？", "Are you the factory or a trading company?")
    if topic == "stock":
        return (f"现在有现货吗？", "Do you have it in stock now?")
    if topic == "specs":
        return ("能提供详细参数吗？比如重量、材质和厚度。",
                "Can you share the detailed specs, such as weight, material and thickness?")
    return None


def translate(text_en, tone, context, quick_text=None):
    """Chinese version of the buyer's message built topic by topic, or None when no known topic is found
    (then the app says the translation needs the AI). quick_text is kept for compatibility."""
    found = topics_of(text_en)
    if not found:
        return None
    f = _facts(text_en, context)
    parts = [_sentences(t, f, context) for t in found]
    parts = [p for p in parts if p]
    o_zh, c_zh, o_en, c_en = TONE.get(tone, TONE["neutral"])
    zh = "".join(z for z, _ in parts)
    en = " ".join(e for _, e in parts)
    return {"zh": o_zh + zh + c_zh, "back_en": (o_en + en + c_en).strip()}


# ---------------------------------------------------------------------------- the simulated supplier
# Chinese markers of each topic in the buyer's message (the sentences above always contain them)
ZH_TOPICS = [("nego", r"单价[¥€$][\d.]+可以吗|目标价"), ("quote", r"最优惠的单价"), ("moq", r"先订\d+|起订量是多少"),
             ("lead", r"交期|天内交货"), ("sample", r"样品"), ("logo", r"logo"), ("packaging", r"包装"),
             ("colour", r"颜色"), ("shipping", r"运费"), ("payment", r"付款方式"), ("cert", r"认证"),
             ("factory", r"工厂还是贸易"), ("stock", r"现货"), ("specs", r"参数")]

_ANALYSES = {}        # reply text -> its English reading (built together with the reply)


def _days(n):
    return "day" if n == 1 else "days"


def _units(n):
    return "unit" if n == 1 else "units"


def _offer(p):
    """A first offer a little under the listing price for the quantity, never under the floor."""
    floor, pct = p.get("floor_price_cny"), p.get("floor_pct") or 0.9
    if floor is None:
        return None
    return max(floor, round(floor / pct * 0.95))


def _to_cny(price, cur, p):
    if cur == "CNY" or price is None:
        return price
    try:
        from core.pricing import fx_rate
        return round(price / fx_rate(cur), 2)
    except Exception:                         # unknown currency: treat as not stated
        return None


def supplier_reply(history, p):
    """Scripted reply in natural seller Chinese to every topic of the buyer's last message, or None."""
    last = next((m["zh"] for m in reversed(history) if m["role"] == "buyer"), "")
    found = [t for t, pat in ZH_TOPICS if re.search(pat, last)]
    if not found:
        return None
    if "nego" in found and "quote" in found:
        found.remove("quote")
    unit = "支" if any(w in (p.get("product_zh") or "").lower() for w in ("球拍", "padel", "racket")) else "件"
    m = re.search(r"订(\d+)[支件]|^.*?(\d+)[支件]的话", last)
    qty = int(next(g for g in m.groups() if g)) if m else int(p.get("qty") or 500)
    moq, lead = p.get("moq") or 1, p.get("lead_time_days") or 15
    offer, floor = _offer(p), p.get("floor_price_cny")
    custom = (p.get("customisation") or "")
    can_logo = custom and "not offered" not in custom.lower() and ("logo" in custom.lower()
                                                                    or "custom" in custom.lower())
    zh, en, hl = [], [], []
    terms = {"unit_price_cny": 0, "price_for_quantity": 0, "moq_units": 0, "lead_time": "", "payment_terms": "",
             "sample_cost": "", "shipping_terms": "", "customization": "", "seller_type": "", "certifications": ""}
    meaning = []

    def say(z, e, highlight=None):
        zh.append(z)
        en.append(e)
        if highlight:
            hl.append(highlight)

    for t in found:
        if t == "quote" and offer:
            say(f"{qty}{unit}的话单价可以给到¥{offer}，", f"For {qty:,} units the unit price can be ¥{offer}.",
                f"单价可以给到¥{offer}")
            terms.update(unit_price_cny=float(offer), price_for_quantity=qty)
            if "moq" not in found:                 # a seller always states the MOQ with a quote
                say(f"起订量{moq}{unit}，", f"MOQ {moq:,} {_units(moq)}.", f"起订量{moq}{unit}")
                terms.update(moq_units=int(moq))
            meaning.append("A first quote slightly under the listing price: there is usually still some room.")
        elif t == "nego" and floor:
            m = re.search(r"单价([¥€$])([\d.]+)可以吗", last)
            target = _to_cny(float(m.group(2)), {"¥": "CNY", "€": "EUR", "$": "USD"}[m.group(1)], p) if m else None
            if target and target >= floor:
                say(f"可以的亲，{qty}{unit}按单价¥{target:g}给您做。", f"Yes, for {qty:,} units we can do ¥{target:g} "
                    f"per unit.", f"单价¥{target:g}")
                terms.update(unit_price_cny=float(target), price_for_quantity=qty)
                meaning.append("They accept your target price: confirm quickly before it changes.")
            else:
                say(f"这个价格已经很实在了，{qty}{unit}的话最低可以做到¥{floor:g}，再低就亏本了。",
                    f"This price is already very fair; for {qty:,} units the lowest we can do is ¥{floor:g}, "
                    f"any lower and we lose money.", f"最低可以做到¥{floor:g}")
                terms.update(unit_price_cny=float(floor), price_for_quantity=qty)
                meaning.append("This is close to their floor price: ask for extras (logo, faster delivery) "
                               "instead of a lower price.")
        elif t == "moq":
            m = re.search(r"先订(\d+)", last)
            if m and int(m.group(1)) < moq:
                say(f"第一次合作可以的，按{m.group(1)}{unit}下单，单价按{moq}{unit}的价格算。",
                    f"For a first order that's fine: {m.group(1)} units, at the price for {moq} units.",
                    "第一次合作可以的")
                meaning.append("They accept a smaller first order.")
            else:
                say(f"起订量{moq}{unit}，", f"The MOQ is {moq:,} units.", f"起订量{moq}{unit}")
            terms.update(moq_units=int(moq))
        elif t == "lead":
            m = re.search(r"能在(\d+)天内交货", last)
            if m and int(m.group(1)) >= lead:
                say(f"{m.group(1)}天内没问题，", f"Within {m.group(1)} days is no problem.", f"{m.group(1)}天内没问题")
                terms.update(lead_time=f"within {m.group(1)} days")
            else:
                say(f"交期{lead}天左右，", f"Lead time about {lead} {_days(lead)}.", f"交期{lead}天左右")
                terms.update(lead_time=f"about {lead} {_days(lead)}")
        elif t == "sample":
            cost, days = p.get("sample_cost_cny"), p.get("sample_days", 5)
            say(f"样品费¥{cost}，下单后可以退还，样品{days}天左右发出，寄到欧洲一般7到10天。",
                f"The sample costs ¥{cost}, refunded when you order; it ships in about {days} days and takes "
                f"7 to 10 days to Europe.", f"样品费¥{cost}")
            terms.update(sample_cost=f"¥{cost}, refunded with the order")
        elif t == "logo":
            if can_logo:
                say("可以印logo，每支加¥5，", "We can print your logo, ¥5 extra per unit.", "每支加¥5")
                terms.update(customization="logo printing, +¥5 per unit")
            else:
                say("这款不支持印logo，", "Logo printing is not offered on this model.", "不支持印logo")
                terms.update(customization="logo printing not offered")
        elif t == "packaging":
            say(f"自己的包装可以，起订量{max(moq, 100)}{unit}，", f"Your own packaging is possible from "
                f"{max(moq, 100)} units.", "自己的包装可以")
        elif t == "colour":
            say(f"颜色可以定制，起订量{max(moq, 100)}{unit}，", f"The colour can be customised from {max(moq, 100)} units.",
                "颜色可以定制")
        elif t == "shipping":
            say("海运、铁路、空运都可以发，运费按重量和体积算，下单前给您报准确运费。",
                "We can ship by sea, rail or air; freight depends on weight and volume, and we'll quote it "
                "exactly before you order.")
            terms.update(shipping_terms="sea, rail or air; freight quoted before the order")
        elif t == "payment":
            say("付款方式是30%定金，发货前付清70%尾款，", "Payment is a 30% deposit and the 70% balance before "
                "shipping.", "30%定金")
            terms.update(payment_terms="30% deposit, 70% before shipping")
        elif t == "cert":
            say("认证证书我这边需要跟工厂确认一下，确认后发给您。",
                "I need to check the certificates with the factory and will send them once confirmed.",
                "需要跟工厂确认")
            meaning.append("No certificate confirmed yet: ask for the documents before paying.")
        elif t == "factory":
            st = p.get("seller_type")
            if st == "factory":
                say("我们是源头工厂，", "We are the factory (direct manufacturer).", "源头工厂")
                terms.update(seller_type="factory")
            else:
                say("我们是贸易公司，和工厂长期合作，", "We are a trading company working with the factory for a "
                    "long time.", "贸易公司")
                terms.update(seller_type="trader")
        elif t == "stock":
            if lead <= 3:
                say("现在有现货，", "It is in stock now.", "有现货")
            else:
                say(f"现在没有现货，需要生产{lead}天左右，", f"Not in stock; production takes about {lead} "
                    f"{_days(lead)}.", "没有现货")
        elif t == "specs":
            spec = [x for x in (p.get("material"), p.get("size")) if x]
            say("参数我整理好发给您，" + ("材质和尺寸见详情页。" if spec else ""),
                "I'll put the specs together and send them" + ("; material and size are on the listing." if spec
                                                              else "."))
    if not zh:
        return None
    text = "亲，您好！" + "".join(zh).rstrip("，") + "。" + ("需要印logo吗？" if "logo" not in found and can_logo
                                                           and "quote" in found else "")
    text = text.replace("。。", "。")
    english = "Hello! " + " ".join(en) + (" Do you need a logo printed?" if text.endswith("需要印logo吗？") else "")
    missing = [s for t, s in [("quote", "What is your best price for my quantity?"),
                              ("sample", "Can you send a sample first?"),
                              ("payment", "What are your payment terms?"),
                              ("logo", "Can you print our logo?")] if t not in found]
    _ANALYSES[text] = {"en": english,
                       "meaning": " ".join(meaning) or "A clear, practical answer; confirm the key terms in writing "
                                                       "before paying.",
                       "highlights": [h for h in hl if h in text],
                       "terms": terms, "suggestions": missing[:3]}
    return text


def analyze(text_zh):
    """English reading of a scripted supplier reply (same shape as the AI analysis), or None."""
    a = _ANALYSES.get(text_zh)
    return (a, None) if a else None
