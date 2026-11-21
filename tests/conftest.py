"""Shared test setup. No test calls the real AI API or the network:
AI answers are simulated and the ECB rate falls back to the sample table."""

import os
import sys
from unittest import mock

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
APP = os.path.join(ROOT, "app.py")


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """Own storage files, no API key, no live FX request, fresh Streamlit caches."""
    import streamlit as st
    from core import messages, orders, pricing, profile

    monkeypatch.setattr(messages, "STORE", str(tmp_path / "conversations.json"))
    monkeypatch.setattr(orders, "STORE", str(tmp_path / "orders.json"))
    monkeypatch.setattr(profile, "STORE", str(tmp_path / "profile.json"))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(pricing, "FX_URLS", [])          # no network: sample rates
    st.cache_data.clear()
    yield


@pytest.fixture
def no_ai():
    """Query translation reports 'no API key' (the state of a machine without a key)."""
    from core import query_translation
    with mock.patch.object(query_translation, "plan_search", return_value=(None, "no API key configured")):
        yield


def run_app(params, timeout=60):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=timeout)
    at.query_params.update(params)
    at.run()
    assert not at.exception, at.exception
    return at


def page_text(at):
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption]
    for kind in (at.success, at.info, at.warning, at.error):
        parts += [str(e.value) for e in kind]
    return " ".join(parts)
