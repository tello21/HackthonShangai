"""Texts that explain how Scoutr works: the FAQ on the home page, "How we score" on every
product page, and the per-marketplace metric rules of the "Trust, explained" section.
They describe what the code really does (core/scoring.py, core/pricing.py), including its
limits. Keep them in sync when the logic changes."""

from html import escape

# ---------------------------------------------------------------------------- the six metrics, per marketplace
# For each metric: the weight, and per platform (what we read, how it becomes 0-100, availability:
# "yes" = shown on that marketplace, "some" = only on some listings, "no" = not shown -> counts as 50).
METRICS = [
    ("Verification", 25, {
        "1688": ("Seller badges.",
                 "Super factory, on-site verified or factory audit = 100 · power merchant = 75 · "
                 "only TrustPass = 40 · none = 0.", "yes"),
        "Taobao": ("Store type.", "Tmall flagship = 100 · Tmall = 85 · enterprise = 55 · personal = 30.", "some"),
        "JD": ("Store type.", "JD self-operated = 100 · flagship = 80 · third-party = 50.", "yes"),
        "Pinduoduo": ("Not shown on Pinduoduo.", "Always counts as 50.", "no"),
    }),
    ("Track record", 20, {
        "1688": ("Years on the platform.", "1 year = 25 · 3 = 60 · 5 = 80 · 8+ = 100.", "yes"),
        "Taobao": ("Years and seller credit (hearts, diamonds, crowns).",
                   "Hearts = 10-30 · diamonds = 40-60 · crowns = 70-90 · gold crown = 100; averaged with years.",
                   "some"),
        "JD": ("Years, when shown.", "1 year = 25 · 3 = 60 · 5 = 80 · 8+ = 100.", "some"),
        "Pinduoduo": ("Years, when shown.", "1 year = 25 · 3 = 60 · 5 = 80 · 8+ = 100.", "some"),
    }),
    ("Customer satisfaction", 25, {
        "1688": ("Service scores out of 5.", "4.0 = 0 · 4.5 = 50 · 5.0 = 100.", "yes"),
        "Taobao": ("Store ratings out of 5.", "4.0 = 0 · 4.5 = 50 · 5.0 = 100.", "yes"),
        "JD": ("Positive reviews and store score.", "90% = 0 · 100% = 100; score 4.0 = 0 · 5.0 = 100.", "yes"),
        "Pinduoduo": ("Store rating and positive reviews, when shown.",
                      "4.0 = 0 · 5.0 = 100; 90% = 0 · 100% = 100.", "some"),
    }),
    ("Loyalty", 10, {
        "1688": ("Repurchase rate.", "0% = 0 · 25% = 50 · 50%+ = 100.", "yes"),
        "Taobao": ("Repurchase rate, rarely shown.", "Usually counts as 50.", "no"),
        "JD": ("Repurchase rate, not shown.", "Counts as 50.", "no"),
        "Pinduoduo": ("Repurchase rate, when shown.", "0% = 0 · 25% = 50 · 50%+ = 100.", "some"),
    }),
    ("Seller type", 10, {
        "1688": ("Factory or trader.", "Factory = 100 · authorized = 70 · trader = 40.", "yes"),
        "Taobao": ("Brand, authorized or reseller.", "Brand official = 100 · authorized = 70 · trader = 40.", "some"),
        "JD": ("Brand, authorized or reseller.", "Brand official (incl. self-operated) = 100 · authorized = 70 · "
               "trader = 40.", "yes"),
        "Pinduoduo": ("Factory or trader.", "Factory = 100 · authorized = 70 · trader = 40.", "some"),
    }),
    ("Sales traction", 10, {
        "1688": ("Orders.", "Ranked against the other 1688 results in your search.", "yes"),
        "Taobao": ("Sales or reviews.", "Ranked against the other Taobao results.", "yes"),
        "JD": ("Reviews (JD hides sales).", "Ranked against the other JD results.", "yes"),
        "Pinduoduo": ("Sales.", "Ranked against the other Pinduoduo results.", "yes"),
    }),
]
PLATFORM_NOTE = {
    "1688": "Factory marketplace with the richest seller data. No price red flag: factory prices are low.",
    "Taobao": "Retail marketplace: Tmall or Taobao store, seller credit, ratings.",
    "JD": "Retail marketplace: self-operated or third-party stores, strong review data.",
    "Pinduoduo": "Group-buying marketplace: no store type, so Verification is always missing.",
}
AVAIL = {"yes": ("Shown", "yes"), "some": ("Sometimes shown", "some"), "no": ("Usually missing → 50", "no")}

RULES = [
    ("Six weighted signals",
     "Verification 25%, track record 20%, customer satisfaction 25%, loyalty 10%, seller type 10%, sales "
     "traction 10%. Each becomes 0-100 with the rules on the right; the score is their weighted sum."),
    ("Missing data is not hidden",
     "A signal the listing doesn't show counts as 50 (average), so a seller with little data can't reach the top. "
     "If the signals we have cover less than 40% of the weights, there is no score: “Not enough data”."),
    ("Red flags cost points",
     "Price under 60% of the median of the same platform in your search: −10 (not on 1688). Product photo showing "
     "a different brand than the title: −30, shown first on the card."),
    ("No false guarantees",
     "A score is a summary of public data, not an inspection or a certification. Bands: Trusted 80+, Good 60-79, "
     "Caution 40-59, High risk under 40."),
]

# ---------------------------------------------------------------------------- "How we score" (product page)
HOW_WE_SCORE = [
    ("How is the trust score calculated?",
     "We read six public signals and give each a value from 0 to 100: Verification (25%), Track record "
     "(20%), Customer satisfaction (25%), Loyalty (10%), Seller type (10%) and Sales traction (10%). The "
     "score is their weighted sum. No AI decides the score: it is a fixed set of rules, and every value is "
     "shown with its reason. The rules per marketplace are on the home page under “Trust, explained”."),
    ("What happens when data is missing?",
     "A missing signal counts as average (50 out of 100), so sellers with little public data can't reach "
     "the top but are not punished as bad either. If the signals we have cover less than 40% of "
     "the weights, we don't show a score at all: you see “Not enough data” and the list of what is missing."),
    ("What is the price red flag?",
     "On Taobao, JD and Pinduoduo, if a product costs less than 60% of the median price of the results "
     "from the same platform in your search, we remove 10 points and say why: prices that low are a common "
     "sign of a problem. It isn't applied to 1688, where factory prices are often far below retail."),
    ("What if the brand looks counterfeit?",
     "If the product photo shows a different brand than the title (for example a well-known racket brand in "
     "the photo and another name in the title), the listing may use a brand without permission. We remove "
     "30 points, after the price red flag, and show “Possible counterfeit brand” as the first reason. Ask the "
     "seller for proof of authorisation before ordering."),
    ("What do the colours mean?",
     "80-100 Trusted (green), 60-79 Good (light green), 40-59 Caution (yellow), 0-39 High risk (red). "
     "Grey means not enough data to score."),
    ("Is the trust score an official verification?",
     "No. It sums up public signals from the listing and the platform; it is not an audit and it is not "
     "endorsed by the marketplaces. Before a large order, ask for a sample and check certifications. Listings "
     "marked “demo data” include some made-up values."),
]

# ---------------------------------------------------------------------------- home FAQ
FAQ = [
    ("What does Scoutr do?",
     "It brings listings from Chinese marketplaces, a trust score for every seller, the delivered price to your "
     "country, translated chat with the supplier and a checkout into one journey for European buyers."),
    ("Which marketplaces can I compare?",
     "1688, Taobao, JD and Pinduoduo. This demo uses a fixed catalog of padel racket listings collected from those "
     "sites, not a live search; listings marked “demo data” include some made-up values."),
    ("How does the search work?",
     "Type what you need in any language. With the AI on, we rewrite it into the words Chinese sellers use in "
     "their titles (not word by word) and match the catalog. Results are sorted by trust; same trust, cheaper first."),
    ("What is included in the delivered price?",
     "The seller's price for your quantity tier, China domestic transport, international shipping (the cheapest of "
     "sea, rail, air and express for your order), insurance (0.5%), import duty for the product and your country, "
     "customs clearance and VAT, converted at the European Central Bank rate of the day."),
    ("How accurate is the delivered price?",
     "The exchange rate is real; freight, duty and VAT rates are estimates. A real quote depends on the customs "
     "code, box size and forwarder, so treat it as a close guide, not an invoice. When a listing has no weight, "
     "we show “not available” instead of guessing."),
    ("How do you calculate supplier trust?",
     "Six rules-based signals: verification 25%, track record 20%, satisfaction 25%, loyalty 10%, seller type "
     "10% and sales traction 10%, converted per marketplace (see “Trust, explained”). Missing signals count as "
     "50; under 40% coverage you see “Not enough data”. Price red flag −10, possible counterfeit brand −30."),
    ("Does a high trust score guarantee a supplier is safe?",
     "No. It is an interpretable summary of public listing and store signals, not an official verification, "
     "inspection, endorsement or buyer protection."),
    ("Can I message Chinese suppliers?",
     "Yes. You write in your language and see the Chinese message before sending, with an English "
     "back-translation; replies come back translated, with what they really mean and the key terms highlighted. "
     "In this demo the supplier's replies are simulated by the AI."),
    ("Can I pay on Scoutr?",
     "The checkout follows real China sourcing: 30% deposit, 70% balance before shipping, then shipping, duty and "
     "VAT on arrival. In this demo payments are simulated: no money moves and no card details are asked for."),
    ("Is Scoutr affiliated with these marketplaces?",
     "No. Showing the marketplace names implies no affiliation or endorsement."),
]


def _details(items):
    return "".join(f"<details class='fq'><summary>{escape(q)}</summary><p>{escape(a)}</p></details>"
                   for q, a in items)


def how_we_score_html():
    return _details(HOW_WE_SCORE)


def faq_html():
    return (f"<div class='faqgrid' id='faq'><div><div class='sectiontag'>Frequently asked questions</div>"
            f"<div class='h2'>Clear answers.<br/>Before you buy.</div><p class='lead'>How search, supplier checks, "
            f"import costs and checkout work in Scoutr.</p></div><div>{_details(FAQ)}</div></div>")


def rules_html():
    return "<div class='principles'>" + "".join(
        f"<div class='principle'><span class='num'>{i:02d}</span><div><div class='pt'>{escape(t)}</div>"
        f"<p>{escape(d)}</p></div></div>" for i, (t, d) in enumerate(RULES, 1)) + "</div>"


def metrics_html(platform):
    """The six metrics as they work on one marketplace; bar = the metric's weight (25% = full)."""
    rows = []
    for name, weight, per in METRICS:
        reads, rule, avail = per[platform]
        label, cls = AVAIL[avail]
        rows.append(
            f"<div class='mrow'><div class='mrow-top'><span>{escape(name)}<span class='avail {cls}'>{label}</span>"
            f"</span><div class='track'><div class='fill' style='width:{weight * 4}%'></div></div>"
            f"<b>{weight}%</b></div><div class='mrow-body'><b>Reads:</b> {escape(reads)}<br/>"
            f"<b>Scores:</b> {escape(rule)}</div></div>")
    return f"<div class='mk-intro'>{escape(PLATFORM_NOTE[platform])}</div>" + "".join(rows)
