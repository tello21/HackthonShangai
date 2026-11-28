# Scoutr

Find a product on Chinese marketplaces (1688, Taobao, JD, Pinduoduo) and see the **real delivered
price**: product + shipping + insurance + duty + customs + VAT, not the price on the original site.

> Demo: results come from a fixed catalog of 13 padel racket listings collected by the team
> (`data/catalog_merged.json`, no live scraping). Listings whose notes start with "DEMO:" contain
> some made-up values and carry a **demo data** label. Freight, duty and VAT are simplified
> estimates, labelled as such in the app; the exchange rate is the live ECB rate when available.
> Missing data is shown as "not available", never made up. Payments are simulated.

## Catalog and photos

`data/catalog_merged.json` is kept exactly as the team delivers it; `core/catalog.py` maps each
record to the app's product card (and keeps its notes, shown under "About this data" on the
product page). Photos: the record's `image` (e.g. `images/1.jpg`) is read from `static/images/`,
which Streamlit serves (`enableStaticServing` in `.streamlit/config.toml`); no image or a missing
file shows a placeholder. To update the catalog, replace the JSON and the photos in `static/images/`.

## Pages

Top bar: Search · Link analyzer · Messages · Profile · FAQ · delivery country and currency.

- **Home** (`views/home.py`): "Search. Compare. Trust. Buy." with one search panel (product ·
  quantity · deliver to · currency; the product field always starts empty). Below: the six steps,
  **Trust, explained** (the real scoring rules; pick 1688, Taobao, JD or Pinduoduo and the six metrics
  show what we read on that marketplace and how it becomes 0-100, with the catalog's own listings and
  scores), the FAQ and a closing call to action.
- **Results**: a compact heading, then four cards per row (three or two on smaller screens), each
  with photo, name, **final price** (delivered, per unit) and **final trust score**; "demo data" and
  counterfeit-risk labels on the photo. Everything else is on the product page.
- **Link analyzer** (`views/link_analyzer.py`): paste a 1688, Taobao, JD or Pinduoduo listing link (or type
  it in the home search) and get the full product page, with the same sections and the same trust score
  and metrics as from the search. For now it works with the listings of our catalog (links are matched
  ignoring tracking parameters; Taobao by item id); other links say they are not in the catalog yet.
- **Messages**: chat with suppliers in your language; they read business Chinese; replies are
  translated and explained.

Results are sorted by **Most trusted** by default (same trust → cheaper first). The
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

AI features (query translation, the Chinese preview of your messages, the supplier's replies) need an
Anthropic API key; without it the app still works and says "not available" where the AI would be used:

```toml
# .streamlit/secrets.toml (git-ignored)   or   export ANTHROPIC_API_KEY=...
ANTHROPIC_API_KEY = "sk-ant-..."
```

One model for every AI feature: `claude-opus-5-5` (change `MODEL` in `core/ai.py`).

## Trust score (`core/scoring.py`)

Pure Python rules, no AI (the AI only extracts raw fields from a listing). Six metrics, each on
0-100: Verification 25%, Track record 20%, Customer satisfaction 25%, Loyalty 10%, Seller type 10%,
Sales traction 10% (sales compared only within the same platform). Missing metrics count as 50
(average; the first spec said 40, changed so the spec's JD and Taobao examples land where expected); under
40% coverage the score is "Not enough data". Price red flag (not on 1688): −10 when the price is below
60% of the same-platform median in the search. Counterfeit risk (`counterfeit_risk: true`, the photo
shows a different brand than the title): −30 after the price red flag, before rounding, and always
the first reason on the card. Pinduoduo listings have no store type, so Verification is missing
there. Bands: Trusted 80+, Good 60-79, Caution 40-59, High risk 0-39. Run the spec's cases with
`python core/scoring.py`. `core/supplier_score.py` maps our product cards to
the raw fields. The product page scores in the same search context as the results list, so both
show the same number.

## Design

From the team's mock-up (`Scoutr — Search. Compare. Trust. Buy.`): ink `#162638`, blue `#17639c`,
lime `#d9f077` for the main buttons and marker strokes, deep blue `#103d5d` for the closing band,
background `#fbfbf7`. Fonts: Space Grotesk (headings, prices, scores) and Inter (text). All CSS is in
`components/style.py`; texts that explain the rules (FAQ, "How we score", the per-marketplace metrics)
are in `views/faq.py` and must follow `core/scoring.py`.

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
  catalog.py           catalog (data/catalog_merged.json) -> product cards, search
  pricing.py           delivered price: ECB rates, shipping modes, duty, VAT
  scoring.py           trust score rules (pure Python, no AI)
  supplier_score.py    maps product cards to the scoring fields
  ai.py                the one Anthropic API wrapper ("not available" reasons instead of errors)
  query_translation.py search -> Chinese buyer query
  messages.py          chat: outgoing translation, simulated supplier, reply analysis, deal terms
  orders.py            orders and the simulated payment flow
  profile.py           buyer profile and default settings
components/            app state + URL, CSS, shared UI pieces
views/                 one module per page (home, results, product, messages, checkout, compare, profile)
data/catalog_merged.json  13 padel racket listings (the team's file, unchanged)
static/images/         product photos (1.jpg ... 13.png)
tests/                 pytest suite
```

Conversations and orders are saved to `conversations.json` / `orders.json` (git-ignored) so the
demo survives a page reload.
