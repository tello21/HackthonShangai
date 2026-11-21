"""'How SourceScan works': questions that open on tap, in two columns on desktop.
The answers describe what the code really does (search, delivered price, trust score),
including its limits. Keep them in sync when the logic changes."""

from html import escape

# "How we score" — shown in the home section and on every product page (keep in sync with core/scoring.py)
HOW_WE_SCORE = [
    ("How is the trust score calculated?",
     "We look at six public signals and give each a value from 0 to 100: Verification (25%), Track record "
     "(20%), Customer satisfaction (25%), Loyalty (10%), Seller type (10%) and Sales traction (10%). The "
     "score is their weighted average, from 0 to 100. No AI decides the score: it is a fixed set of rules, "
     "and every value is shown on the product page with its reason."),
    ("How do you compare 1688, Taobao, JD and Pinduoduo?",
     "Each platform shows trust differently, so we convert each to the same 0-100 scale. Verification: on "
     "1688 a super factory or on-site audit badge is 100, 实力商家 75, only 诚信通 40; on Taobao a Tmall "
     "flagship is 100 and a personal store 30; on JD self-operated is 100 and a third-party seller 50; on "
     "Pinduoduo, where listings show no store type, verification counts as missing. Years active (8+ years = 100) and "
     "Taobao credit levels (hearts, diamonds, crowns) give the track record; 5-point service ratings and "
     "positive-review rates give satisfaction; the repurchase rate gives loyalty. Sales are only compared "
     "with other results from the same platform, because each platform counts them differently."),
    ("What happens when data is missing?",
     "A missing signal counts as average (50 out of 100), so sellers with little public data can't reach "
     "the top but are not punished as bad either. If the signals we have cover less than 40% of "
     "the weights, we don't show a score at all: you see “Not enough data” and the list of what is missing."),
    ("What is the price red flag?",
     "On Taobao, JD and Pinduoduo, if a product costs less than 60% of the median price of similar results "
     "from the same platform in your search, we remove 10 points and say why: prices that low are a common "
     "sign of a problem. It isn't applied to 1688, where factory prices are often far below retail."),
    ("What if the brand looks counterfeit?",
     "If the product photo shows a different brand than the title (for example a well-known racket brand in "
     "the photo and another name in the title), the listing may use a brand without permission. We remove "
     "30 points, after the price red flag, and show “Possible counterfeit brand” as the first reason on the "
     "card. Ask the seller for proof of authorisation before ordering."),
    ("What do the colours mean?",
     "80-100 Trusted (green), 60-79 Good (light green), 40-59 Caution (yellow), 0-39 High risk (red). "
     "Grey means not enough data to score."),
    ("Is the trust score an official verification?",
     "No. It sums up public signals from the listing and the platform; it is not an audit and it is not "
     "endorsed by the marketplaces. Before a large order, ask for a sample and check certifications. In "
     "this demo, listings marked “demo data” include some made-up values."),
]

FAQ = [
    ("Search", [
        ("How does the search work?",
         "Type what you need in any language. With the AI turned on, we rewrite it into the words Chinese "
         "sellers actually put in their titles (not a word-by-word translation), then look for matching "
         "listings. Every result shows the delivered price to your country and the seller's trust score."),
        ("Which marketplaces do you search?",
         "1688, Taobao, JD and Pinduoduo. In this demo the results come from a fixed catalog of padel racket "
         "listings collected from those sites, not a live search; listings marked “demo data” include some "
         "made-up values. With Link paste you can analyse a listing from any of the four."),
        ("Why are results sorted by trust?",
         "A cheap price is worth nothing if the seller is unreliable, so the most trusted sellers come first; "
         "sellers without enough data come after the scored ones. Sellers with the same score are ordered by "
         "delivered price. You can switch to “Lowest price” or “Lowest MOQ” at any time."),
        ("What does Link paste do?",
         "Paste a product link and get the same analysis as a product page: delivered price, trust score and "
         "contact. We don't open marketplace pages ourselves, so for an unknown link add a screenshot or the "
         "page text and the AI reads it."),
    ]),
    ("Trust", HOW_WE_SCORE),
    ("Delivered price", [
        ("How is the delivered price calculated?",
         "Seller price for your quantity tier, plus China domestic transport, international shipping, "
         "insurance (0.5%), import duty for the product category and your country, customs clearance and VAT. "
         "Everything is converted at the European Central Bank rate of the day and shown line by line."),
        ("Which shipping method do you use?",
         "The cheapest one for your order among sea, rail, air and express, by chargeable weight and with each "
         "method's minimum charge: express for a few units, rail or sea for large orders. On the product page "
         "you can pick another method and see its transit time."),
        ("How accurate is the estimate?",
         "The exchange rate is real; freight, duty and VAT rates are estimates. A real quote depends on the "
         "customs code, the box size and the forwarder, so treat it as a close guide, not an invoice."),
        ("Why do some prices show “not available”?",
         "We never guess. If a listing has no weight, shipping can't be calculated; if the product category is "
         "unknown, the duty can't. Ask the supplier for the missing detail from Messages."),
    ]),
    ("Messages and orders", [
        ("Can I talk to suppliers in my language?",
         "Yes. Write in English or your language; before sending you see the Chinese message the supplier will "
         "get, with an English back-translation. Replies come back translated, with what they really mean and "
         "the key terms highlighted."),
        ("How does paying work?",
         "As in real China sourcing: 30% deposit to start production, 70% balance before shipping, and "
         "shipping, duty, VAT and customs on arrival. In this demo payments are simulated: no money moves and no "
         "card details are ever asked for."),
    ]),
]


def how_we_score_html():
    return "".join(f"<details class='faq-q'><summary>{escape(q)}</summary><div class='faq-a'>{escape(a)}</div>"
                   f"</details>" for q, a in HOW_WE_SCORE)


def faq_html():
    groups = []
    for title, items in FAQ:
        qa = "".join(f"<details class='faq-q'><summary>{escape(q)}</summary><div class='faq-a'>{escape(a)}</div>"
                     f"</details>" for q, a in items)
        groups.append(f"<div class='faq-group'><div class='faq-h'>{escape(title)}</div>{qa}</div>")
    return ("<div class='faq'><div class='faq-title'>How SourceScan works</div>"
            f"<div class='faq-cols'>{''.join(groups)}</div></div>")
