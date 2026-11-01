"""Provider contract. A provider is a thing that turns a prompt into text.

Two rules keep this honest:
  1. `available()` never guesses — it answers "do I have credentials", nothing else.
  2. `complete()` raises on failure instead of returning a canned string. A
     fallback that silently invents text is worse than an outage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class LLMUnavailable(RuntimeError):
    """Every provider in the chain refused. Carries why, so the UI can say why."""

    def __init__(self, attempts: list[Attempt]):
        self.attempts = attempts
        detail = "; ".join(f"{a.provider}: {a.error}" for a in attempts) or "no providers configured"
        super().__init__(detail)


@dataclass
class Attempt:
    provider: str
    error: str
    ms: int = 0


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    cached: bool = False
    latency_ms: int = 0
    attempts: list[Attempt] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "cached": self.cached,
            "latency_ms": self.latency_ms,
            "attempts": [a.__dict__ for a in self.attempts],
        }


@runtime_checkable
class Provider(Protocol):
    name: str
    model: str

    def available(self) -> bool: ...

    def complete(
        self, prompt: str, *, system: str | None = None, json_mode: bool = False
    ) -> str: ...
