"""'How SourceScan works': questions that open on tap, in two columns on desktop.
The answers describe what the code really does (search, delivered price, trust score),
including its limits. Keep them in sync when the logic changes."""

from html import escape

FAQ = [
    ("Search", [
        ("How does the search work?",
         "Type what you need in any language. With the AI turned on, we rewrite it into the words Chinese "
         "sellers actually put in their titles (not a word-by-word translation), then look for matching "
         "listings. Every result shows the delivered price to your country and the seller's trust score."),
        ("Which marketplaces do you search?",
         "Yiwugo listings are read live from yiwugo.com and tagged “Live”. For 1688, Taobao and JD we use a "
         "demo catalog for now, tagged “Sample”. With Link paste you can analyse a listing from any of the four."),
        ("Why are results sorted by trust?",
         "A cheap price is worth nothing if the seller is unreliable, so the most trusted sellers come first. "
         "Sellers with the same score are ordered by delivered price. You can switch to “Lowest price” or "
         "“Lowest MOQ” at any time."),
        ("What does Link paste do?",
         "Paste a product link and get the same analysis as a product page: delivered price, trust score and "
         "contact. We don't open marketplace pages ourselves, so for an unknown link add a screenshot or the "
         "page text and the AI reads it."),
    ]),
    ("Trust", [
        ("How is the trust score calculated?",
         "Every seller starts at 50. A factory adds 10, a store 3, a trading company loses 5. Years active add "
         "up to 15. Verified badges (verified supplier, trade assurance, onsite inspection…) add up to 10 each. "
         "A high response rate and many repeat buyers add points, low ones remove some; a high dispute rate "
         "removes 10. The result "
         "stays between 0 and 100, and every reason is listed on the product page."),
        ("What do the colours mean?",
         "Green is 80 or more (high trust), yellow 60 to 79 (medium), red below 60 (low). Grey “n/a” means we "
         "know too little about the seller to give a score."),
        ("Why does a seller show “Trust n/a”?",
         "We only score a seller when we know at least two facts about them, for example the seller type and "
         "the years active. Showing a neutral number for an unknown seller would look like a real score, so "
         "we show “n/a” instead."),
        ("Is the trust score final?",
         "No. It uses simple rules on the data a listing shows, and some of that data is from our demo catalog. "
         "Always ask for a sample and check certifications before a large order: the product page tells you "
         "what is still unknown."),
    ]),
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
         "unknown, the duty can't. On the product page you can add the weight yourself and the price appears, "
         "marked “user-provided”."),
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


def faq_html():
    groups = []
    for title, items in FAQ:
        qa = "".join(f"<details class='faq-q'><summary>{escape(q)}</summary><div class='faq-a'>{escape(a)}</div>"
                     f"</details>" for q, a in items)
        groups.append(f"<div class='faq-group'><div class='faq-h'>{escape(title)}</div>{qa}</div>")
    return ("<div class='faq'><div class='faq-title'>How SourceScan works</div>"
            f"<div class='faq-cols'>{''.join(groups)}</div></div>")
