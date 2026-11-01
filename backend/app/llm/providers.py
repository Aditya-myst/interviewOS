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
GEMINI_LIST_URL = "https://generativelanguage.googleapis.com/v1beta/models"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_LIST_URL = "https://api.groq.com/openai/v1/models"

# ── Model selection ───────────────────────────────────────────────────────────
# Hard-coded model names are how this integration breaks: a name that was valid
# last quarter answers 404 "no longer available to new users", and the app looks
# broken when it is only out of date. So the default is "auto": ask the provider
# which models the key can actually call, then pick with an explicit, testable
# ordering. Pin a name in GEMINI_MODEL / GROQ_MODEL when you want determinism.

_GEMINI_NOISE = ("embedding", "aqa", "imagen", "veo", "tts", "audio", "live", "image")


def pick_gemini_model(ids: list[str]) -> str | None:
    """Prefer cheapest usable chat model: latest stable Flash, not Lite, not preview."""
    def score(mid: str) -> tuple:
        low = mid.lower()
        version = 0.0
        for chunk in low.replace("-", ".").split("."):
            try:
                version = max(version, float(chunk))
            except ValueError:
                continue
        return (
            "flash" in low,                       # Flash: free-tier quota, fast
            "preview" not in low and "exp" not in low,
            "lite" not in low,
            version,
        )

    usable = [m for m in ids if "generate" not in m.lower() or True]
    usable = [m for m in usable if not any(n in m.lower() for n in _GEMINI_NOISE)]
    usable = [m for m in usable if "gemini" in m.lower()]
    return max(usable, key=score) if usable else None


_GROQ_NOISE = ("whisper", "tts", "guard", "embed", "vision-preview")


def pick_groq_model(ids: list[str]) -> str | None:
    """Prefer a large open-weight chat model over a small/fast one."""
    def score(mid: str) -> tuple:
        low = mid.lower()
        size = 0
        for token in low.replace("-", " ").replace("_", " ").split():
            if token.endswith("b") and token[:-1].isdigit():
                size = max(size, int(token[:-1]))
        return (size, "instruct" in low or "versatile" in low, "llama" in low)

    usable = [m for m in ids if not any(n in m.lower() for n in _GROQ_NOISE)]
    return max(usable, key=score) if usable else None


_resolved: dict[str, str] = {}


def list_gemini_models(api_key: str, timeout: float) -> list[str]:
    resp = httpx.get(GEMINI_LIST_URL, headers={"x-goog-api-key": api_key}, timeout=timeout)
    if resp.status_code >= 400:
        raise ProviderHTTPError("gemini", resp.status_code, _error_message(resp))
    out = []
    for row in resp.json().get("models", []):
        methods = row.get("supportedGenerationMethods") or []
        if "generateContent" in methods:
            out.append(str(row.get("name", "")).removeprefix("models/"))
    return [m for m in out if m]


def list_groq_models(api_key: str, timeout: float) -> list[str]:
    resp = httpx.get(
        GROQ_LIST_URL, headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout
    )
    if resp.status_code >= 400:
        raise ProviderHTTPError("groq", resp.status_code, _error_message(resp))
    return [str(r["id"]) for r in resp.json().get("data", []) if r.get("id")]


def resolve_model(provider: str, configured: str | None, api_key: str, timeout: float) -> str:
    """`configured` wins when set; otherwise ask the provider once per process."""
    if configured and configured.lower() not in ("", "auto"):
        return configured
    if provider in _resolved:
        return _resolved[provider]
    if provider == "gemini":
        picked = pick_gemini_model(list_gemini_models(api_key, timeout))
    else:
        picked = pick_groq_model(list_groq_models(api_key, timeout))
    if not picked:
        raise RuntimeError(f"{provider}: no usable model returned by the provider")
    _resolved[provider] = picked
    return picked


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str | None, timeout: float):
        self.api_key = api_key
        self._model = model
        self.timeout = timeout

    @property
    def model(self) -> str:
        """Resolved lazily: naming a model costs a network call, and a probe with
        no key configured must never make one."""
        if self._model and self._model.lower() not in ("", "auto"):
            return self._model
        if not self.api_key:
            return "unresolved (no key)"
        return resolve_model("gemini", self._model, self.api_key, self.timeout)

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

    def __init__(self, api_key: str, model: str | None, timeout: float):
        self.api_key = api_key
        self._model = model
        self.timeout = timeout

    @property
    def model(self) -> str:
        if self._model and self._model.lower() not in ("", "auto"):
            return self._model
        if not self.api_key:
            return "unresolved (no key)"
        return resolve_model("groq", self._model, self.api_key, self.timeout)

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
