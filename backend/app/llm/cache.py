"""Response cache: sha256(model | schema_version | prompt) -> payload.

Two backends with the same interface. Memory when there is no database (tests,
CI, a laptop without .env), Postgres `llm_cache` when there is one. The point is
the same either way: a repeated prompt must not spend free-tier quota.
"""
from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Protocol

from sqlalchemy import text

from app.db import get_session


def cache_key(model: str, prompt: str, schema_version: int) -> str:
    raw = f"{model}|{schema_version}|{prompt}".encode()
    return hashlib.sha256(raw).hexdigest()


class Cache(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...
    def put(self, key: str, payload: dict[str, Any], *, model: str, snippet: str) -> None: ...


class MemoryCache:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            return self._data.get(key)

    def put(self, key: str, payload: dict[str, Any], *, model: str, snippet: str) -> None:
        with self._lock:
            self._data[key] = payload


class DbCache:
    """Reads and writes public.llm_cache. Service-role only in production — the
    table has RLS on and no policies, and prompts contain resume text."""

    def get(self, key: str) -> dict[str, Any] | None:
        try:
            with get_session() as session:
                row = session.execute(
                    text(
                        "select response from public.llm_cache "
                        "where key = :k and expires_at > now()"
                    ),
                    {"k": key},
                ).first()
                if row is None:
                    return None
                session.execute(
                    text("update public.llm_cache set hits = hits + 1 where key = :k"),
                    {"k": key},
                )
                return row[0]
        except Exception:  # noqa: BLE001 — a cache miss is never an outage
            return None

    def put(self, key: str, payload: dict[str, Any], *, model: str, snippet: str) -> None:
        try:
            with get_session() as session:
                session.execute(
                    text(
                        "insert into public.llm_cache (key, model, schema_version, prompt_snippet, response) "
                        "values (:k, :m, :v, :s, cast(:r as jsonb)) "
                        "on conflict (key) do update set response = excluded.response, "
                        "prompt_snippet = excluded.prompt_snippet"
                    ),
                    {"k": key, "m": model, "v": 1, "s": snippet[:500], "r": json.dumps(payload)},
                )
        except Exception:  # noqa: BLE001
            return
