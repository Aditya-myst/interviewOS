"""Concrete providers: Gemini Flash (free tier) and Groq (open-weight fallback).

Both are plain httpx calls. No SDK, because the SDKs are the part that breaks:
the free tiers change models more often than they change HTTP.
"""
from __future__ import annotations

import json

import httpx

from app.config import get_settings


class ProviderHTTPError(RuntimeError):
    """A provider said no, and here is what it actually said.

    httpx's raise_for_status() gives you "Client error '400 Bad Request' for url
    ..." and drops the response body — which is the only part that tells you
    whether the key is wrong, the model name is wrong, or the daily quota is
    gone. That message is what we surface instead.
    """

    def __init__(self, provider: str, status: int, message: str, raw: str = ""):
        self.provider = provider
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}" + (f" | {raw[:200]}" if raw else ""))


def _error_message(resp: httpx.Response) -> str:
    """Gemini and Groq both put the useful sentence in different places."""
    try:
        data = resp.json()
    except Exception:  # noqa: BLE001 — not JSON, fall back to the text
        return resp.text.strip()[:300] or resp.reason_phrase

    err = data.get("error") if isinstance(data, dict) else None
    if isinstance(err, dict):
        bits = [str(err.get("status") or err.get("type") or "").strip(), str(err.get("message") or "").strip()]
        joined = ": ".join(b for b in bits if b)
        if joined:
            return joined[:300]
    if isinstance(err, str):
        return err[:300]
    return json.dumps(data)[:300]


def _post(provider: str, url: str, **kwargs) -> dict:
    resp = httpx.post(url, **kwargs)
    if resp.status_code >= 400:
        raise ProviderHTTPError(provider, resp.status_code, _error_message(resp))
    return resp.json()


GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        body: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        data = _post(
            self.name,
            GEMINI_URL.format(model=self.model),
            headers={"x-goog-api-key": self.api_key, "content-type": "application/json"},
            json=body,
            timeout=self.timeout,
        )
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:  # blocked prompt, safety stop, etc.
            raise RuntimeError(f"unexpected Gemini payload: {json.dumps(data)[:200]}") from exc


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str, timeout: float):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, prompt: str, *, system: str | None = None, json_mode: bool = False) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        body: dict = {"model": self.model, "messages": messages, "temperature": 0.2}
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        data = _post(
            self.name,
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
            },
            json=body,
            timeout=self.timeout,
        )
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"unexpected Groq payload: {json.dumps(data)[:200]}") from exc


def default_chain() -> list:
    """Primary then fallback, built from settings. Order is configurable."""
    s = get_settings()
    known = {
        "gemini": GeminiProvider(s.gemini_api_key, s.gemini_model, s.llm_timeout_s),
        "groq": GroqProvider(s.groq_api_key, s.groq_model, s.llm_timeout_s),
    }
    chain = []
    for name in (s.llm_provider, s.llm_fallback):
        provider = known.get(name)
        if provider and provider not in chain:
            chain.append(provider)
    return chain
