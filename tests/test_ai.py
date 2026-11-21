"""The shared AI wrapper and the query translation (API simulated)."""

import json
import time
from types import SimpleNamespace as NS
from unittest import mock

import anthropic

from core import ai, query_translation

PLAN = {"detected_language": "Italian", "intent_en": "Carbon fiber padel rackets",
        "query_zh": "碳纤维板式网球拍", "query_zh_meaning_en": "carbon fiber padel racket",
        "pinyin": "tàn xiānwéi bǎnshì wǎngqiú pāi", "alternative_queries_zh": ["padel球拍 碳纤维"],
        "keywords_en": ["padel racket", "carbon"], "clarify": ["Carbon grade (e.g. 3K, 12K, 18K)"]}


def fake_response(stop="end_turn", text=json.dumps(PLAN)):
    # a thinking block FIRST: the colleague's original code read content[0].text and broke here
    return NS(stop_reason=stop, content=[NS(type="thinking", thinking=""), NS(type="text", text=text)])


def call_with(resp):
    client = mock.MagicMock()
    client.beta.messages.create.return_value = resp
    with mock.patch.object(anthropic, "Anthropic", return_value=client), \
         mock.patch.object(ai, "_api_key", "test-key"):
        return query_translation.plan_search("racchetta da padel in carbonio"), client


def test_reads_text_block_after_thinking_and_uses_one_model():
    (plan, err), client = call_with(fake_response())
    assert err is None and plan["query_zh"] == "碳纤维板式网球拍"
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
