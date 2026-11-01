"""The gateway is the part that must not lie, so it gets real tests:

- primary fails -> fallback answers, and the failure is recorded
- every provider fails -> LLMUnavailable with reasons, never a canned string
- a repeated prompt is served from cache and does not call the provider again
- a provider that returns invalid JSON is treated as a failure, not cached
"""
import json

import pytest

from app.llm.base import LLMUnavailable
from app.llm.cache import MemoryCache
from app.llm.gateway import Gateway


class FakeProvider:
    def __init__(self, name, text="ok", fail=False, available=True):
        self.name = name
        self.model = f"{name}-model"
        self.text = text
        self.fail = fail
        self._available = available
        self.calls = 0

    def available(self):
        return self._available

    def complete(self, prompt, *, system=None, json_mode=False):
        self.calls += 1
        if self.fail:
            raise RuntimeError("upstream 500")
        return self.text


def gateway(*providers, cache=None):
    return Gateway(chain=list(providers), cache=cache or MemoryCache(), schema_version=1)


def test_falls_back_and_records_the_failure():
    primary = FakeProvider("gemini", fail=True)
    fallback = FakeProvider("groq", text="from groq")

    result = gateway(primary, fallback).complete("q")

    assert result.text == "from groq"
    assert result.provider == "groq"
    assert primary.calls == 1
    assert result.attempts[0].provider == "gemini"
    assert "upstream 500" in result.attempts[0].error


def test_no_provider_configured_raises_with_reasons():
    with pytest.raises(LLMUnavailable) as exc:
        gateway(FakeProvider("gemini", available=False)).complete("q")
    assert "not configured" in str(exc.value)


def test_every_provider_failing_raises_rather_than_inventing_text():
    with pytest.raises(LLMUnavailable):
        gateway(FakeProvider("gemini", fail=True), FakeProvider("groq", fail=True)).complete("q")


def test_second_identical_prompt_is_cached():
    provider = FakeProvider("gemini", text="cached body")
    gw = gateway(provider)

    first = gw.complete("same prompt")
    second = gw.complete("same prompt")

    assert provider.calls == 1
    assert first.cached is False
    assert second.cached is True
    assert second.text == "cached body"


def test_different_prompts_do_not_share_a_cache_entry():
    provider = FakeProvider("gemini")
    gw = gateway(provider)
    gw.complete("a")
    gw.complete("b")
    assert provider.calls == 2


def test_invalid_json_is_a_failure_not_a_cache_hit():
    bad = FakeProvider("gemini", text="not json")
    good = FakeProvider("groq", text=json.dumps({"ok": True}))

    def validator(text):
        json.loads(text)  # raises on the bad provider

    result = gateway(bad, good).complete("prompt", json_mode=True, validator=validator)

    assert result.provider == "groq"
    assert result.cached is False
    assert json.loads(result.text) == {"ok": True}
