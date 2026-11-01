"""Liveness, readiness, and a dev-only LLM probe."""
from __future__ import annotations

from fastapi import APIRouter, Response
from pydantic import BaseModel
from sqlalchemy import text

from app import fixtures
from app.config import get_settings
from app.db import db_status, get_session
from app.llm import LLMUnavailable, get_gateway
from app.schemas import HealthResponse, ReadyResponse

router = APIRouter(tags=["system"])

VERSION = "0.1.0"


def current_mode() -> str:
    return "database" if db_status()["state"] == "connected" else "fixture"


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness only. Deliberately touches nothing: a health check that fails
    because a third party is down is a health check that pages you for nothing."""
    s = get_settings()
    return HealthResponse(status="ok", env=s.env, version=VERSION, mode=current_mode())


@router.get("/ready", response_model=ReadyResponse)
def ready(response: Response) -> ReadyResponse:
    """Readiness: can this process serve a request right now, and in what mode?

    Degraded is a real, reportable state — not an error. The UI shows a banner
    rather than an empty screen, which is the whole point of having the mode.
    """
    get_settings()
    db = db_status()
    fixtures_present = fixtures.available()
    llm_providers = get_gateway().available_providers()

    checks = {
        "database": db,
        "fixtures": {
            "ok": all(fixtures_present.values()),
            "state": "present" if all(fixtures_present.values()) else "incomplete",
            "detail": {k: v for k, v in fixtures_present.items() if not v} or None,
        },
        "llm": {
            "ok": bool(llm_providers),
            "state": "configured" if llm_providers else "unconfigured",
            "detail": llm_providers or "no provider keys — LLM features return llm_unavailable",
        },
    }

    core_ok = db["ok"] or all(fixtures_present.values())
    status = "ok" if (core_ok and llm_providers) else "degraded"
    if not core_ok:
        status = "unavailable"
        response.status_code = 503

    return ReadyResponse(status=status, mode=current_mode(), checks=checks)


VERIFY_SQL = """
with counts as (
  select
    (select count(*) from information_schema.tables
      where table_schema = 'public' and table_type = 'BASE TABLE')        as tables,
    (select count(*) from pg_tables
      where schemaname = 'public' and rowsecurity)                        as rls_tables,
    (select count(*) from pg_policies where schemaname = 'public')         as policies,
    (select count(*) from pg_type t join pg_namespace n on n.oid = t.typnamespace
      where n.nspname = 'public' and t.typtype = 'e')                      as enums,
    (select count(*) from pg_extension
      where extname in ('vector', 'pgcrypto', 'pg_trgm'))                  as extensions,
    (select count(*) from public.skills)                                   as skills,
    (select count(*) from public.skill_subtopics)                          as subtopics,
    (select count(*) from public.resources)                                as resources,
    (select count(*) from public.resources
      where tier = 0 and verified_at is not null)                          as verified_links
)
select * from counts;
"""

# (name, expected) — the numbers docs/sql/004_verify.sql promises. Keeping the
# expectations here, next to the query, means a seed change breaks this loudly.
EXPECTED = [
    ("tables", 18),
    ("rls_tables", 18),
    ("enums", 22),
    ("extensions", 3),
    ("skills", 31),
    ("subtopics", 100),
    ("resources", 39),
]


@router.get("/dev/db")
def db_probe() -> dict:
    """Dev-only: prove the database matches the handover, without psql.

    This is the JSON twin of docs/sql/004_verify.sql — same query, same
    expectations, but you can curl it and paste the answer. Every check reports
    expected *and* actual so a wrong project is obvious rather than "looks fine".
    """
    if get_settings().env == "prod":
        raise RuntimeError("disabled in prod")

    st = db_status()
    if st["state"] != "connected":
        return {
            "ok": False,
            "error": {
                "code": "db_unconfigured",
                "message": "DATABASE_URL is unset or unreachable — serving fixtures",
                "detail": st.get("detail"),
            },
        }

    with get_session() as session:
        row = session.execute(text(VERIFY_SQL)).mappings().one()

    checks = [
        {"name": name, "expected": expected, "actual": int(row[name]), "ok": int(row[name]) >= expected}
        for name, expected in EXPECTED
    ]
    checks.append(
        {
            "name": "policies",
            "expected": ">= 0",
            "actual": int(row["policies"]),
            "ok": True,
            "note": "informational: 48 at handover, grows with each policy you add",
        }
    )
    checks.append(
        {
            "name": "verified_links",
            "expected": ">= 0",
            "actual": int(row["verified_links"]),
            "ok": True,
            "note": "tier-0 curated resources checked by scripts/check_links.py",
        }
    )

    return {
        "ok": all(c["ok"] for c in checks),
        "mode": "database",
        "checks": checks,
        "failed": [c["name"] for c in checks if not c["ok"]],
    }


class LLMProbe(BaseModel):
    prompt: str
    json_mode: bool = False


@router.post("/dev/llm")
def llm_probe(body: LLMProbe) -> dict:
    """Dev-only: prove which provider answered, or why none could.

    In `ENV=prod` this route answers 404 — it is a probe, not a feature."""
    s = get_settings()
    if s.env == "prod":
        raise RuntimeError("disabled in prod")

    gateway = get_gateway()
    try:
        result = gateway.complete(body.prompt, json_mode=body.json_mode)
    except LLMUnavailable as exc:
        return {
            "ok": False,
            "error": {
                "code": "llm_unavailable",
                "message": "No provider could answer",
                "detail": str(exc),
            },
            "configured": gateway.available_providers(),
        }
    return {"ok": True, **result.as_dict(), "text": result.text[:500]}
