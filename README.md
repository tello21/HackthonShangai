# SourceScan

Find a product on Chinese marketplaces (1688, Taobao, JD, Yiwugo) and see the **real delivered
price**: product + shipping + insurance + duty + customs + VAT, not the price on the original site.

> Demo: results come from a **sample catalog** (no scraping). Freight, duty and VAT are simplified
> sample estimates, labelled as such in the app; the exchange rate is the live ECB rate when
> available. Missing data is shown as "not available", never made up. Payments are simulated.

## The three sections (bar at the top of the home page)

| 🔗 Link paste | 🔎 Sourcing (default) | 💬 Messages |
|---|---|---|
| Paste a link: a link to a sample-catalog product opens its full analysis; for any other link, add a screenshot or the page text and the AI reads it | Search in any language → translated for Chinese marketplaces → Amazon-style list with delivered prices and supplier scores | Chat with suppliers in your language; they read business Chinese; replies are translated and explained |

Results are sorted by **Most trusted** by default (same trust → cheaper first). Below the search, the
home page explains how search, the delivered price and the trust score work (`views/faq.py`). The
**Profile** page lists your orders and keeps your settings: name, company, email and the default
country, currency and quantity for every search (saved in `profile.json`, git-ignored).

From a product page: delivered price per shipping method (sea, rail, air, express) with the full
breakdown, supplier score with reasons, **Contact supplier**, and **Order** → checkout with a
simulated 30% deposit / 70% balance → order tracking.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

AI features (query translation, messages, reading screenshots) need an Anthropic API key; without
it the app still works and says "not available" where the AI would be used:

```toml
# .streamlit/secrets.toml (git-ignored)   or   export ANTHROPIC_API_KEY=...
ANTHROPIC_API_KEY = "sk-ant-..."
```

One model for every AI feature: `claude-opus-5-5` (change `MODEL` in `core/ai.py`).

## Trust score (`core/scoring.py`)

Pure Python rules, no AI (the AI only extracts raw fields from a listing). Six metrics, each on
0-100: Verification 25%, Track record 20%, Customer satisfaction 25%, Loyalty 10%, Seller type 10%,
Sales traction 10% (sales compared only within the same platform). Missing metrics count as 40; under
40% coverage the score is "Not enough data". Price red flag (not on 1688): −10 when the price is below
60% of the same-platform median in the search. Bands: Trusted 80+, Good 60-79, Caution 40-59,
High risk 0-39. Run the spec's cases with `python core/scoring.py`. `core/supplier_score.py` maps
our product cards (sample catalog, live Yiwugo, Link paste) to the raw fields.

## Live Yiwugo listings

Each search also reads real listings from yiwugo.com (PR #1): real titles, prices, MOQ, photos,
shops and links, tagged **Live** in the results (everything else is tagged **Sample**). Yiwugo
listings have no weight, so the buyer adds it on the product page to get the delivered price
(marked "user-provided"). English names come from the AI, or from a small glossary without a key.

This reads Yiwugo's website search, not an official API: it can stop working when Yiwugo changes
its site, and automated access may conflict with Yiwugo's terms. Speed: each Yiwugo request takes
~5 s from Europe, so the search token is fetched in the background at start-up and reused, the list is
built from the search answer (~5 s per new search, instant when repeated within 10 minutes), and
listing details are fetched in the background so product pages open at once. Turn it off with `YIWUGO_LIVE=0`; the app then uses only the sample catalog.

## Tests

```bash
pip install pytest
python -m pytest
```

The tests simulate the AI and never call the network.

## Code layout

```
app.py                 page setup + router
core/                  business logic, no UI
  catalog.py           sample catalog (data/catalog.json), search, demo links
  pricing.py           delivered price: ECB rates, shipping modes, duty, VAT
  supplier_score.py    supplier reliability score (sample rules; replace with the real model)
  ai.py                the one Anthropic API wrapper ("not available" reasons instead of errors)
  query_translation.py search -> Chinese buyer query
  messages.py          chat: outgoing translation, simulated supplier, reply analysis, deal terms
  listing.py           Link paste: AI reading of screenshot/text + rule-based fallback
  orders.py            orders and the simulated payment flow
  yiwugo.py            live Yiwugo search (PR #1), switch YIWUGO_LIVE
components/            app state + URL, CSS, shared UI pieces
views/                 one module per page (home, results, product, link_paste, messages, checkout, compare)
data/catalog.json      20 sample products
tests/                 pytest suite
```

Conversations and orders are saved to `conversations.json` / `orders.json` (git-ignored) so the
demo survives a page reload.
