"""The gateway: cache -> primary -> fallback -> explicit failure.

There is no fourth step that invents an answer. Callers that need to survive a
model outage implement their own deterministic path (parsing does; question
generation will not, and says so with `llm_unavailable`).
"""
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from app.config import get_settings
from app.db import db_status
from app.llm.base import Attempt, LLMResult, LLMUnavailable, Provider
from app.llm.cache import Cache, DbCache, MemoryCache, cache_key
from app.llm.providers import default_chain


class Gateway:
    def __init__(
        self,
        chain: list[Provider] | None = None,
        cache: Cache | None = None,
        *,
        schema_version: int | None = None,
    ) -> None:
        settings = get_settings()
        self.chain: list[Provider] = chain if chain is not None else default_chain()
        if cache is None:
            cache = DbCache() if db_status()["state"] == "connected" else MemoryCache()
        self.cache = cache
        self.schema_version = (
            schema_version if schema_version is not None else settings.llm_cache_version
        )

    def available_providers(self) -> list[str]:
        return [p.name for p in self.chain if p.available()]

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        json_mode: bool = False,
        validator: Callable[[str], Any] | None = None,
    ) -> LLMResult:
        """`validator` runs on the text before it is cached: a provider that
        answers with invalid JSON is a provider failure, not a cache entry."""
        attempts: list[Attempt] = []
        for provider in self.chain:
            if not provider.available():
                attempts.append(Attempt(provider.name, "not configured"))
                continue

            try:
                model = provider.model
            except Exception as exc:  # noqa: BLE001 — model lookup is a network call too
                attempts.append(
                    Attempt(provider.name, f"{type(exc).__name__}: {exc}"[:300], 0)
                )
                continue

            key = cache_key(model, prompt, self.schema_version)
            hit = self.cache.get(key)
            if hit is not None:
                text = hit.get("text") if isinstance(hit, dict) else None
                if text:
                    if validator is not None:
                        try:
                            validator(text)
                        except Exception:  # noqa: BLE001 — stale/invalid entry, ignore it
                            hit = None
                    if hit is not None:
                        return LLMResult(
                            text=text,
                            provider=provider.name,
                            model=model,
                            cached=True,
                            latency_ms=0,
                            attempts=attempts,
                        )

            started = time.monotonic()
            try:
                text = provider.complete(prompt, system=system, json_mode=json_mode)
                if validator is not None:
                    validator(text)
            except Exception as exc:  # noqa: BLE001 — every provider failure looks the same here
                attempts.append(
                    Attempt(
                        provider.name,
                        f"{type(exc).__name__}: {exc}"[:300],
                        int((time.monotonic() - started) * 1000),
                    )
                )
                continue

            self.cache.put(key, {"text": text}, model=model, snippet=prompt[:500])
            return LLMResult(
                text=text,
                provider=provider.name,
                model=model,
                cached=False,
                latency_ms=int((time.monotonic() - started) * 1000),
                attempts=attempts,
            )

        raise LLMUnavailable(attempts)


_gateway: Gateway | None = None


def get_gateway() -> Gateway:
    global _gateway
    if _gateway is None:
        _gateway = Gateway()
    return _gateway
