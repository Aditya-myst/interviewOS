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


def test_provider_http_error_keeps_the_providers_own_sentence(monkeypatch):
    """httpx.raise_for_status() throws away the response body, which is the only
    place the reason lives ("API key not valid", "model not found", quota)."""

    from app.llm import providers

    class Resp:
        status_code = 400
        text = "{}"

        def json(self):
            return {"error": {"status": "INVALID_ARGUMENT", "message": "API key not valid."}}

    monkeypatch.setattr(providers.httpx, "post", lambda *a, **k: Resp())
    p = providers.GeminiProvider("k" * 20, "gemini-2.5-flash", 5)
    try:
        p.complete("hi")
    except providers.ProviderHTTPError as exc:
        assert "API key not valid" in str(exc)
        assert "INVALID_ARGUMENT" in str(exc)
        assert exc.status == 400
    else:
        raise AssertionError("expected ProviderHTTPError")


def test_llm_config_route_never_prints_a_key(monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSECRETSECRETSECRET1234")
    from app.llm import providers

    monkeypatch.setattr(providers, "list_gemini_models", lambda *a, **k: ["gemini-3.8-flash"])
    providers._resolved.clear()
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        body = TestClient(app).get("/dev/llm").json()
        dumped = str(body)
        assert "AIzaSECRETSECRETSECRET" not in dumped
        assert body["chain"]
        for row in body["chain"]:
            assert row["key_hint"] is None or len(row["key_hint"]) <= 7
        rows = {row["provider"]: row for row in body["chain"]}
        assert rows["gemini"]["model"] == "gemini-3.8-flash"
        assert rows["gemini"]["model_source"] == "auto"
        # no Groq key in this test, so the row says so instead of guessing a model
        assert rows["groq"]["configured"] is False
        assert rows["groq"]["model"] == "unresolved (no key)"
    finally:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        get_settings.cache_clear()


def test_pickers_prefer_a_stable_flash_and_a_large_open_model():
    """Model names expire ("no longer available to new users"). The picker must
    choose from the provider's live list, not from a constant in this repo."""
    from app.llm.providers import pick_gemini_model, pick_groq_model

    gem = ["gemini-2.5-pro", "gemini-3.8-flash-preview-09", "gemini-3.8-flash",
           "gemini-3.8-flash-lite", "text-embedding-004", "imagen-4"]
    assert pick_gemini_model(gem) == "gemini-3.8-flash"

    groq = ["whisper-large-v3", "tts-1", "llama-3.1-8b-instant", "gpt-oss-120b",
            "llama-3.3-70b-versatile"]
    assert pick_groq_model(groq) == "gpt-oss-120b"


def test_pickers_return_none_instead_of_a_guess():
    from app.llm.providers import pick_gemini_model, pick_groq_model

    assert pick_gemini_model([]) is None
    assert pick_groq_model(["whisper-large-v3", "tts-1"]) is None


def test_a_cached_answer_does_not_wait_behind_a_dead_primary():
    """Measured in the wild: primary timed out at 45 s, fallback had the answer
    cached, and the cached call still cost 45 s because the primary was tried
    first. Cache is now searched across the whole chain before any network call."""
    import time

    cache = MemoryCache()
    primary = FakeProvider("primary", fail=True)
    fallback = FakeProvider("fallback", text="answer")
    gw = gateway(primary, fallback, cache=cache)

    first = gw.complete("same prompt")
    assert first.provider == "fallback" and not first.cached
    assert primary.calls == 1

    started = time.monotonic()
    second = gw.complete("same prompt")
    elapsed = time.monotonic() - started

    assert second.cached is True
    assert second.provider == "fallback"
    assert primary.calls == 1, "the dead primary must not be called again"
    assert fallback.calls == 1
    assert elapsed < 0.1


def test_gemini_request_shape_is_pure_and_thinking_is_opt_out():
    """The 45 s ReadTimeout came from Gemini deciding how hard to think about
    "reply with ok". Turning thinking off is a one-env-var switch, and the body
    it produces is testable without a network call."""
    from app.llm.providers import gemini_body

    plain = gemini_body("hi")
    assert "thinkingConfig" not in plain["generationConfig"]

    thinking_off = gemini_body("hi", thinking="off")
    assert thinking_off["generationConfig"]["thinkingConfig"] == {"thinkingBudget": 0}

    js = gemini_body("hi", json_mode=True, system="be terse")
    assert js["generationConfig"]["responseMimeType"] == "application/json"
    assert js["systemInstruction"]["parts"][0]["text"] == "be terse"


def test_a_blank_fallback_still_leaves_a_second_provider(monkeypatch):
    """LLM_FALLBACK= (blank) or a typo must not silently reduce the chain to one."""
    from app.config import get_settings
    from app.llm.providers import default_chain

    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_FALLBACK", "")
    get_settings.cache_clear()
    try:
        names = [p.name for p in default_chain()]
        assert names[0] == "groq"
        assert "gemini" in names
    finally:
        monkeypatch.delenv("LLM_FALLBACK", raising=False)
        get_settings.cache_clear()


def test_the_suite_ignores_a_local_env_file_for_llm_settings():
    """What the conftest pins is what the app sees, whatever is in backend/../.env."""
    from app.config import get_settings

    s = get_settings()
    assert (s.llm_provider, s.llm_fallback) == ("groq", "gemini")
    assert s.gemini_api_key == "" and s.groq_api_key == ""
