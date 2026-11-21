"""The shared AI wrapper, the query translation and the listing reader (API simulated)."""

import json
import time
from types import SimpleNamespace as NS
from unittest import mock

import anthropic

from core import ai, listing, query_translation

PLAN = {"detected_language": "Italian", "intent_en": "Canvas tote bags with a printed logo",
        "query_zh": "帆布袋定制logo", "query_zh_meaning_en": "custom logo canvas bag",
        "pinyin": "fānbù dài dìngzhì logo", "alternative_queries_zh": ["帆布手提袋 印logo"],
        "keywords_en": ["tote bag", "canvas"], "clarify": ["Canvas weight (e.g. 12 oz)"]}


def fake_response(stop="end_turn", text=json.dumps(PLAN)):
    # a thinking block FIRST: the colleague's original code read content[0].text and broke here
    return NS(stop_reason=stop, content=[NS(type="thinking", thinking=""), NS(type="text", text=text)])


def call_with(resp):
    client = mock.MagicMock()
    client.beta.messages.create.return_value = resp
    with mock.patch.object(anthropic, "Anthropic", return_value=client), \
         mock.patch.object(ai, "_api_key", "test-key"):
        return query_translation.plan_search("borsa di tela con logo"), client


def test_reads_text_block_after_thinking_and_uses_one_model():
    (plan, err), client = call_with(fake_response())
    assert err is None and plan["query_zh"] == "帆布袋定制logo"
    kw = client.beta.messages.create.call_args.kwargs
    assert kw["model"] == ai.MODEL == "claude-opus-5-5"
    assert kw["fallbacks"] == "default"
    assert kw["output_config"]["format"]["type"] == "json_schema"


def test_refusal_truncation_and_no_key_are_reported():
    assert call_with(fake_response(stop="refusal"))[0] == (None, "the request was declined")
    assert call_with(fake_response(stop="max_tokens"))[0] == (None, "the answer was cut off")
    ai.set_api_key(None)
    t = time.time()
    assert query_translation.plan_search("borsa") == (None, "no API key configured")
    assert time.time() - t < 0.5            # answered at once, without loading the SDK


# ---------------------------------------------------------------- listing reader
AI_LISTING = {
    "title_cn": "12安帆布手提袋 可定制logo", "title_en": "12 oz canvas tote bag, custom logo",
    "platform": "", "moq": 100, "tiers": [{"min_qty": 500, "price_cny": 7.2}, {"min_qty": 100, "price_cny": 8.5}],
    "material": "12 oz cotton canvas", "size": "38 x 42 cm", "weight_g": 180, "production_days": 15,
    "customisation": "Logo printing", "category": "bags",
    "supplier": {"name_cn": "温州某某袋业有限公司", "name_en": "", "city": "Wenzhou", "seller_type": "factory",
                 "store_type": "unknown", "years": 11, "badges_cn": ["诚信通", "实力商家"],
                 "taobao_credit_level": "", "service_scores_5pt": [4.7, 0], "positive_review_pct": 0,
                 "repurchase_rate_pct": 0, "sales_count": 1200},
}


def test_read_screenshot_builds_a_card_without_inventing():
    with mock.patch.object(ai, "ask", return_value=(AI_LISTING, None)) as ask:
        card, err = listing.read_listing(image=b"\x89PNG fake", media_type="image/png",
                                         url="https://detail.1688.com/offer/612345.html")
    assert err is None
    content = ask.call_args.args[1][0]["content"]
    assert content[0]["type"] == "image" and content[0]["source"]["media_type"] == "image/png"
    assert card["platform"] == "1688"                       # from the link, since the AI left it empty
    assert card["tiers"] == [(100, 8.5), (500, 7.2)]        # sorted
    assert card["weight_kg"] == 0.18
    s = card["supplier"]
    assert s["name"] is None                                # "" -> not available
    assert s["repurchase_rate_pct"] is None                 # 0 -> not available
    assert s["badges_cn"] == ["诚信通", "实力商家"] and s["seller_type"] == "factory" and s["type"] == "factory"
    assert s["store_type"] is None and s["service_scores_5pt"] == [4.7] and s["sales_count"] == 1200
    # the AI only extracts; the score comes from core/scoring.py
    from core.supplier_score import trust_for
    r = trust_for(card)
    assert r["metrics"][0]["value"] == 75 and r["metrics"][0]["reason"].startswith("实力商家")


def test_rule_based_fallback_still_reads_text():
    card = listing.parse_listing(listing.SAMPLE_LISTING)
    assert card["moq"] == 100 and card["weight_kg"] == 0.18 and card["platform"] == "1688"
    assert card["material"].startswith("Pure cotton canvas")
