#!/usr/bin/env python3
"""InterviewOS environment doctor.

Run from the repo root:
    uv run python scripts/verify_env.py

Checks: env vars -> Postgres -> pgvector -> Gemini -> Groq -> web search -> local data files.
Prints a PASS/FAIL table and exits non-zero if anything critical fails.
No secrets are printed. Model names are discovered, not hardcoded.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
results: list[tuple[str, bool, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


def load_env() -> None:
    """Minimal .env loader so this runs before the app exists."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        record(".env present", False, "missing .env at repo root")
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.split(" #")[0].strip().strip('"').strip("'")
        if key and value and not os.environ.get(key):
            os.environ[key] = value
    record(".env present", True, str(env_path))


def mask(value: str | None) -> str:
    if not value:
        return "<empty>"
    return f"{value[:6]}...{value[-4:]}" if len(value) > 12 else "<short>"


def check_required_keys() -> None:
    required = ["GEMINI_API_KEY", "GROQ_API_KEY", "SUPABASE_URL", "DATABASE_URL"]
    missing = [k for k in required if not os.environ.get(k)]
    record("required keys", not missing, "missing: " + ", ".join(missing) if missing
           else f"gemini={mask(os.environ.get('GEMINI_API_KEY'))} groq={mask(os.environ.get('GROQ_API_KEY'))}")

    url = os.environ.get("SUPABASE_URL", "")
    db = os.environ.get("DATABASE_URL", "")
    ref_ok = True
    detail = ""
    if url and db and "://" in db:
        ref_url = url.split("//")[-1].split(".")[0]
        try:
            userinfo = db.split("://", 1)[1].split("@")[-2] if db.count("@") > 1 else db.split("://", 1)[1].split("@")[0]
            ref_db = userinfo.split(":")[0].replace("postgres.", "")
            ref_ok = ref_url == ref_db
            detail = f"supabase ref {ref_url} vs db ref {ref_db}"
        except Exception as exc:  # noqa: BLE001
            ref_ok, detail = False, f"could not parse DATABASE_URL ({exc})"
    record("project ref matches", ref_ok, detail or "skipped")


def check_database() -> None:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        record("postgres connect", False, "DATABASE_URL not set")
        return
    try:
        import psycopg
    except Exception:
        record("postgres connect", False, "psycopg not installed: uv add 'psycopg[binary]'")
        return
    dsn = url.replace("+psycopg", "")
    if "@" in dsn and dsn.count("@") > 1:
        record("postgres connect", False, "password contains a raw '@' — percent-encode it as %40")
        return
    try:
        with psycopg.connect(dsn, connect_timeout=12) as conn:
            dbname = conn.execute("select current_database()").fetchone()[0]
            ver = conn.execute("show server_version").fetchone()[0]
            record("postgres connect", True, f"db={dbname} server={ver}")
            ext = conn.execute(
                "select extversion from pg_extension where extname = 'vector'"
            ).fetchone()
            record("pgvector installed", bool(ext),
                   f"v{ext[0]}" if ext else "run: create extension if not exists vector;")
    except Exception as exc:  # noqa: BLE001
        record("postgres connect", False, f"{type(exc).__name__}: {exc}"[:200])


def _pick_model(models: list[str], needle: str) -> str | None:
    for m in models:
        if needle in m:
            return m
    return models[0] if models else None


def check_gemini() -> None:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        record("gemini", False, "GEMINI_API_KEY not set")
        return
    try:
        import httpx
    except Exception:
        record("gemini", False, "httpx not installed: uv add httpx")
        return
    base = "https://generativelanguage.googleapis.com/v1beta"
    try:
        with httpx.Client(timeout=25) as client:
            resp = client.get(f"{base}/models", headers={"x-goog-api-key": key})
            if resp.status_code != 200:
                record("gemini", False, f"models list {resp.status_code}: {resp.text[:120]}")
                return
            names = [m["name"].split("/")[-1] for m in resp.json().get("models", [])
                     if "generateContent" in m.get("supportedGenerationMethods", [])]
            model = _pick_model(names, "2.5-flash") or _pick_model(names, "flash")
            if not model:
                record("gemini", False, "no generateContent model available")
                return
            body = {"contents": [{"parts": [{"text": "Reply with the single word: ok"}]}],
                    "generationConfig": {"maxOutputTokens": 8, "temperature": 0}}
            r2 = client.post(f"{base}/models/{model}:generateContent",
                             headers={"x-goog-api-key": key}, json=body)
            ok = r2.status_code == 200
            snippet = ""
            if ok:
                try:
                    parts = r2.json()["candidates"][0]["content"]["parts"]
                    snippet = "".join(p.get("text", "") for p in parts).strip()[:20]
                except Exception:  # noqa: BLE001
                    snippet = "(no text parsed)"
            record("gemini", ok, f"model={model} -> {snippet}" if ok else f"{r2.status_code}: {r2.text[:120]}")
    except Exception as exc:  # noqa: BLE001
        record("gemini", False, f"{type(exc).__name__}: {exc}"[:160])


def check_groq() -> None:
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        record("groq", False, "GROQ_API_KEY not set")
        return
    try:
        import httpx
    except Exception:
        record("groq", False, "httpx not installed")
        return
    headers = {"Authorization": f"Bearer {key}"}
    try:
        with httpx.Client(timeout=25, headers=headers) as client:
            resp = client.get("https://api.groq.com/openai/v1/models")
            if resp.status_code != 200:
                record("groq", False, f"models list {resp.status_code}: {resp.text[:120]}")
                return
            names = [m["id"] for m in resp.json().get("data", [])]
            model = next((m for m in names if "llama" in m and "instant" in m), None) \
                or next((m for m in names if "qwen" in m), None) or (names[0] if names else None)
            if not model:
                record("groq", False, "no chat model available")
                return
            r2 = client.post("https://api.groq.com/openai/v1/chat/completions", json={
                "model": model,
                "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
                "max_tokens": 8, "temperature": 0,
            })
            ok = r2.status_code == 200
            detail = f"model={model} -> {r2.json()['choices'][0]['message']['content'][:20]!r}" \
                if ok else f"{r2.status_code}: {r2.text[:140]}"
            record("groq", ok, detail)
    except Exception as exc:  # noqa: BLE001
        record("groq", False, f"{type(exc).__name__}: {exc}"[:160])


def check_search() -> None:
    backend = os.environ.get("SEARCH_BACKEND", "ddgs")
    if backend != "ddgs":
        record("web search", True, f"backend={backend} (not exercised here)")
        return
    try:
        from ddgs import DDGS
    except Exception:
        record("web search", False, "ddgs not installed: uv add ddgs")
        return
    try:
        with DDGS() as ddgs:
            hits = [(r.get("title"), r.get("href")) for r in ddgs.text(
                "fastapi dependency injection", max_results=2)]
        record("web search", bool(hits), f"{len(hits)} results, top: {hits[0][1][:60] if hits else '-'}")
    except Exception as exc:  # noqa: BLE001
        record("web search", False, f"{type(exc).__name__}: {exc}"[:160])


def check_data_files() -> None:
    try:
        import yaml
    except Exception:
        record("data files", False, "pyyaml not installed: uv add pyyaml")
        return
    try:
        tax = yaml.safe_load((ROOT / "data" / "taxonomy.yaml").read_text(encoding="utf-8"))
        cur = yaml.safe_load((ROOT / "data" / "curated.yaml").read_text(encoding="utf-8"))
        skills = tax["skills"]
        subs = sum(len(s["subtopics"]) for s in skills)
        res = sum(len(r) for v in cur["catalogue"].values() for r in v.values())
        record("data files", True, f"{len(skills)} skills / {subs} subtopics / {res} curated resources")
    except FileNotFoundError:
        record("data files", False, "data/taxonomy.yaml or data/curated.yaml missing")
    except Exception as exc:  # noqa: BLE001
        record("data files", False, f"{type(exc).__name__}: {exc}"[:160])


def check_contracts() -> None:
    need = ["contracts/openapi.yaml", "contracts/types.ts", "contracts/ENUMS.md",
            "contracts/fixtures/dashboard.json"]
    missing = [p for p in need if not (ROOT / p).exists()]
    record("contracts present", not missing, "missing: " + ", ".join(missing) if missing else "all 4 present")


def main() -> int:
    print(f"\nInterviewOS environment doctor — {ROOT}\n")
    load_env()
    check_required_keys()
    check_contracts()
    check_database()
    check_gemini()
    check_groq()
    check_search()
    check_data_files()

    width = max(len(name) for name, _, _ in results)
    critical = {name for name, _, _ in results}
    for name, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = [name for name, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("Fix first: " + failed[0])
        return 1
    print("Environment is green. Next: the Day-1 backend skeleton.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
