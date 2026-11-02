"""Persistence: the only place the pipeline touches Postgres.

Two rules:

1. **The schema is the contract.** Every insert here names columns that exist in
   docs/sql/001_init.sql. There is no `create_all`, no migration runner, and no
   "just one extra column" — the database is handed over, not managed by the app.
2. **Nothing is written without evidence.** `upsert_skills` refuses a row whose
   evidence list is empty, mirroring the product rule at the storage layer, so a
   caller that skipped the quote gate fails loudly instead of quietly.

When there is no database the API stays in fixture mode and these functions are
never called — that is a supported state, not an error path.
"""
from __future__ import annotations

import json
import logging
import uuid as uuid_mod

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.parsing.extract import Document
from app.parsing.jd import ParsedJD
from app.parsing.resume import ParsedResume
from app.prep.dashboard import build_dashboard
from app.prep.priority import ScoredSkill
from app.prep.profile import counts, coverage_by_category
from app.prep.roadmap import build_roadmap

log = logging.getLogger(__name__)

# parse_status is an enum of ('ok','degraded') in 001_init.sql. "unparseable" is a
# response concept, not a storage one: an unreadable document is stored as degraded
# with the reason in parse_meta, so the row never pretends the parse succeeded.
PARSE_STATUS_DB = {"ok": "ok", "unparseable": "degraded", "degraded": "degraded"}


class UserUnresolved(RuntimeError):
    """No signed-in user and no DEMO_USER_ID. Says how to fix it, in the message."""

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class EvidenceRequired(RuntimeError):
    pass


# ── user resolution ───────────────────────────────────────────────────────────
def resolve_user(session: Session) -> tuple[str, str]:
    """Which profile owns this data.

    Auth arrives properly in a later phase. Until then: an explicit DEMO_USER_ID
    wins; otherwise, in a non-production environment, a single existing profile is
    used and the response says so (`user_source: single_profile`). Anything
    ambiguous refuses rather than guessing whose resume this is.
    """
    settings = get_settings()

    if settings.demo_user_id:
        row = session.execute(
            text("select id from public.profiles where id = cast(:id as uuid)"),
            {"id": settings.demo_user_id},
        ).first()
        if row is None:
            raise UserUnresolved(
                f"DEMO_USER_ID={settings.demo_user_id} does not exist in public.profiles. "
                "Create the user in Supabase → Authentication → Users (the trigger makes the "
                "profile row), then copy its id."
            )
        return str(row[0]), "demo_user_id"

    rows = session.execute(text("select id from public.profiles limit 2")).all()
    if len(rows) == 1:
        log.info("resolved user from the single existing profile — set DEMO_USER_ID to pin this")
        return str(rows[0][0]), "single_profile"
    if not rows:
        raise UserUnresolved(
            "public.profiles is empty. Create one user in Supabase → Authentication → Users "
            "(auto-confirm), then set DEMO_USER_ID in .env."
        )
    raise UserUnresolved(
        f"{len(rows)}+ profiles exist — refusing to guess. Set DEMO_USER_ID in .env."
    )


# ── writes ────────────────────────────────────────────────────────────────────
def save_resume(
    session: Session,
    *,
    user_id: str,
    document: Document,
    parsed: ParsedResume,
    parse_status: str = "ok",
    storage_path: str | None = None,
    mime_type: str | None = None,
) -> str:
    payload = parsed.as_json()
    parse_meta = {
        "method": parsed.stats.get("method"),
        "parse_version": 5,
        "model": None,                       # deterministic pass: no model was used
        "warnings": document.warnings,
        "experience_basis": parsed.experience_basis,
        "stats": parsed.stats,
    }
    row = session.execute(
        text(
            """
            insert into public.resumes
              (user_id, filename, mime_type, size_bytes, storage_path, raw_text,
               parse_status, parse_meta, skills, projects, experience_years)
            values
              (cast(:user_id as uuid), :filename, :mime_type, :size_bytes, :storage_path,
               :raw_text, cast(:parse_status as public.parse_status),
               cast(:parse_meta as jsonb), cast(:skills as jsonb),
               cast(:projects as jsonb), :experience_years)
            returning id
            """
        ),
        {
            "user_id": user_id,
            "filename": document.filename,
            "mime_type": mime_type,
            "size_bytes": document.size_bytes,
            "storage_path": storage_path,
            "raw_text": document.text,
            "parse_status": PARSE_STATUS_DB.get(parse_status, "degraded"),
            "parse_meta": json.dumps(parse_meta),
            "skills": json.dumps(payload["skills"]),
            "projects": json.dumps([]),
            "experience_years": parsed.experience_years,
        },
    ).one()
    return str(row[0])


def save_jd(session: Session, *, user_id: str, body: str, parsed: ParsedJD) -> str:
    row = session.execute(
        text(
            """
            insert into public.job_descriptions
              (user_id, title, company, role, seniority, min_years_experience, body,
               parse_status, requirements, interview_rounds, rounds_inferred, topics)
            values
              (cast(:user_id as uuid), :title, :company, :role,
               cast(:seniority as public.seniority), :min_years, :body,
               'ok', cast(:requirements as jsonb), cast(:rounds as text[]),
               :rounds_inferred, cast(:topics as text[]))
            returning id
            """
        ),
        {
            "user_id": user_id,
            "title": parsed.title,
            "company": parsed.company,
            "role": parsed.role,
            "seniority": parsed.seniority,
            "min_years": parsed.min_years_experience,
            "body": body,
            "requirements": json.dumps(parsed.as_json()["requirements"]),
            "rounds": parsed.interview_rounds,
            "rounds_inferred": parsed.rounds_inferred,
            "topics": parsed.topics,
        },
    ).one()
    return str(row[0])


UPSERT_SKILL = text(
    """
    insert into public.candidate_skills
      (user_id, skill_id, status, claimed_level, verified_level, expected_level,
       confidence, jd_importance, interview_relevance, gap, priority, priority_band,
       explanation, in_resume, in_jd, evidence)
    values
      (cast(:user_id as uuid), :skill_id, cast(:status as public.skill_status),
       cast(:claimed_level as public.proficiency_level),
       cast(:verified_level as public.verified_level),
       cast(:expected_level as public.verified_level),
       cast(:confidence as numeric(3,2)), cast(:jd_importance as numeric(3,2)),
       cast(:interview_relevance as numeric(3,2)), cast(:gap as numeric(3,2)),
       cast(:priority as numeric(4,3)), cast(:priority_band as public.priority_band),
       :explanation, :in_resume, :in_jd, cast(:evidence as jsonb))
    on conflict (user_id, skill_id) do update set
      status = excluded.status,
      claimed_level = excluded.claimed_level,
      verified_level = coalesce(excluded.verified_level, public.candidate_skills.verified_level),
      expected_level = excluded.expected_level,
      confidence = excluded.confidence,
      jd_importance = excluded.jd_importance,
      interview_relevance = excluded.interview_relevance,
      gap = excluded.gap,
      priority = excluded.priority,
      priority_band = excluded.priority_band,
      explanation = excluded.explanation,
      in_resume = excluded.in_resume,
      in_jd = excluded.in_jd,
      evidence = excluded.evidence,
      updated_at = now()
    """
)


def upsert_skills(session: Session, *, user_id: str, rows: list[ScoredSkill]) -> int:
    written = 0
    for row in rows:
        if not row.evidence:
            # the storage-layer version of "no quote, no row"
            raise EvidenceRequired(f"{row.skill_id} has no evidence — refusing to store it")
        session.execute(
            UPSERT_SKILL,
            {
                "user_id": user_id,
                "skill_id": row.skill_id,
                "status": row.status,
                "claimed_level": row.claimed_level,
                "verified_level": row.verified_level,
                "expected_level": row.expected_level,
                "confidence": row.confidence,
                "jd_importance": row.jd_importance,
                "interview_relevance": row.interview_relevance,
                "gap": row.gap,
                "priority": row.priority,
                "priority_band": row.priority_band,
                "explanation": row.explanation,
                "in_resume": row.in_resume,
                "in_jd": row.in_jd,
                "evidence": json.dumps(row.evidence),
            },
        )
        written += 1
    return written


# ── reads ─────────────────────────────────────────────────────────────────────
PROFILE_SQL = text(
    """
    select cs.skill_id, cs.status::text, cs.claimed_level::text, cs.verified_level::text,
           cs.expected_level::text, cs.confidence, cs.jd_importance, cs.interview_relevance,
           cs.gap, cs.priority, cs.priority_band::text, cs.explanation, cs.in_resume, cs.in_jd,
           cs.evidence, cs.last_assessed_at, s.name, s.category
    from public.candidate_skills cs
    join public.skills s on s.id = cs.skill_id
    where cs.user_id = cast(:user_id as uuid)
    order by cs.priority desc, cs.skill_id
    """
)


def profile_payload(session: Session, *, user_id: str) -> dict | None:
    """The stored profile, in the same shape build_profile() produces.

    None means "this user has no candidate_skills rows yet" — the caller decides to
    serve fixtures instead, and says so in the header.
    """
    rows = session.execute(PROFILE_SQL, {"user_id": user_id}).mappings().all()
    if not rows:
        return None

    skills = [
        {
            "skill_id": row["skill_id"],
            "name": row["name"],
            "category": row["category"],
            "status": row["status"],
            "claimed_level": row["claimed_level"],
            "verified_level": row["verified_level"],
            "expected_level": row["expected_level"],
            "confidence": float(row["confidence"]),
            "jd_importance": float(row["jd_importance"]),
            "interview_relevance": float(row["interview_relevance"]),
            "gap": float(row["gap"]),
            "priority": float(row["priority"]),
            "priority_band": row["priority_band"],
            "explanation": row["explanation"],
            "in_resume": row["in_resume"],
            "in_jd": row["in_jd"],
            "last_assessed_at": row["last_assessed_at"].isoformat()
            if row["last_assessed_at"]
            else None,
            "evidence": row["evidence"] or [],
        }
        for row in rows
    ]

    band_tally = {key: 0 for key in ("critical", "high", "medium", "low")}
    for skill in skills:
        band_tally[skill["priority_band"]] += 1

    provisional = not any(skill["verified_level"] for skill in skills)
    return {
        "provisional": provisional,
        "counts": {
            **band_tally,
            "verified": sum(1 for s in skills if s["status"] == "verified"),
            "unverified": sum(1 for s in skills if s["status"] == "unverified"),
        },
        "coverage_by_category": _coverage(skills),
        "skills": skills,
    }


def _coverage(skills: list[dict]) -> list[dict]:
    """Reuse the pure helpers by adapting stored rows to the ScoredSkill interface."""

    class _Row:
        def __init__(self, data: dict):
            self.category = data["category"]
            self.status = data["status"]

    return coverage_by_category([_Row(s) for s in skills])  # type: ignore[arg-type]


RESOURCES_SQL = text(
    """
    select id, url, title, provider, kind::text, is_paid, license, verified_at,
           curated_skill_id, curated_subtopic_id
    from public.resources
    where curated_skill_id = any(:skill_ids)
      and is_dead = false
    """
)


def catalogue_for(session: Session, *, skill_ids: list[str]) -> dict[tuple[str, str], list[dict]]:
    """Resource rows grouped by (skill, subtopic) — the roadmap's raw material."""
    if not skill_ids:
        return {}
    rows = session.execute(RESOURCES_SQL, {"skill_ids": skill_ids}).mappings().all()
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        item = dict(row)
        item["id"] = str(item["id"])
        item["verified_at"] = item["verified_at"].isoformat() if item["verified_at"] else None
        key = (item["curated_skill_id"], item["curated_subtopic_id"])
        grouped.setdefault(key, []).append(item)
    return grouped


def _scored_rows(session: Session, user_id: str) -> list:
    """Stored rows back into the shape the dashboard/roadmap builders expect."""
    class _Row:
        pass

    out = []
    for row in session.execute(PROFILE_SQL, {"user_id": user_id}).mappings().all():
        item = _Row()
        item.skill_id = row["skill_id"]
        item.name = row["name"]
        item.category = row["category"]
        item.status = row["status"]
        item.claimed_level = row["claimed_level"]
        item.verified_level = row["verified_level"]
        item.expected_level = row["expected_level"]
        item.confidence = float(row["confidence"])
        item.jd_importance = float(row["jd_importance"])
        item.interview_relevance = float(row["interview_relevance"])
        item.gap = float(row["gap"])
        item.priority = float(row["priority"])
        item.priority_band = row["priority_band"]
        item.explanation = row["explanation"]
        item.in_resume = row["in_resume"]
        item.in_jd = row["in_jd"]
        item.evidence = row["evidence"] or []
        item.as_json = lambda _row=row: {
            "skill_id": _row["skill_id"], "name": _row["name"], "category": _row["category"],
            "status": _row["status"], "claimed_level": _row["claimed_level"],
            "verified_level": _row["verified_level"], "expected_level": _row["expected_level"],
            "confidence": float(_row["confidence"]), "jd_importance": float(_row["jd_importance"]),
            "interview_relevance": float(_row["interview_relevance"]),
            "gap": float(_row["gap"]), "priority": float(_row["priority"]),
            "priority_band": _row["priority_band"], "explanation": _row["explanation"],
            "in_resume": _row["in_resume"], "in_jd": _row["in_jd"],
            "last_assessed_at": None, "evidence": _row["evidence"] or [],
        }
        out.append(item)
    return out


def dashboard_payload(session: Session, *, user_id: str) -> dict | None:
    """None when this user has no scored skills — the caller serves fixtures."""
    rows = _scored_rows(session, user_id)
    if not rows:
        return None

    role = session.execute(
        text(
            "select coalesce(p.target_role, (select title from public.job_descriptions "
            "where user_id = p.id order by created_at desc limit 1)) "
            "from public.profiles p where p.id = cast(:user_id as uuid)"
        ),
        {"user_id": user_id},
    ).scalar()

    interviews = [
        {
            "session_id": str(row["id"]),
            "mode": row["mode"],
            "channel": row["channel"],
            "score": float(row["overall_score"]) if row["overall_score"] is not None else None,
            "duration_minutes": row["duration_minutes"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        for row in session.execute(
            text(
                "select s.id, s.mode, s.channel, r.overall_score, s.duration_minutes, s.created_at "
                "from public.interview_sessions s "
                "left join public.interview_reports r on r.session_id = s.id "
                "where s.user_id = cast(:user_id as uuid) order by s.created_at desc limit 10"
            ),
            {"user_id": user_id},
        ).mappings().all()
    ]

    return build_dashboard(rows, target_role=role, interviews=interviews)


def roadmap_payload(session: Session, *, user_id: str) -> dict | None:
    rows = _scored_rows(session, user_id)
    if not rows:
        return None
    skill_ids = sorted({row.skill_id for row in rows if row.priority_band != "low"})
    catalogue = catalogue_for(session, skill_ids=skill_ids) if skill_ids else {}
    role = session.execute(
        text(
            "select coalesce(p.target_role, (select title from public.job_descriptions "
            "where user_id = p.id order by created_at desc limit 1)) "
            "from public.profiles p where p.id = cast(:user_id as uuid)"
        ),
        {"user_id": user_id},
    ).scalar()
    return build_roadmap(rows, catalogue, target_role=role)


def latest_resume(session: Session, *, user_id: str) -> dict | None:
    row = session.execute(
        text(
            """
            select id, filename, parse_status::text, experience_years, created_at,
                   jsonb_array_length(skills) as skills_count
            from public.resumes where user_id = cast(:user_id as uuid)
            order by created_at desc limit 1
            """
        ),
        {"user_id": user_id},
    ).mappings().first()
    return dict(row) if row else None


def latest_jd(session: Session, *, user_id: str) -> dict | None:
    row = session.execute(
        text(
            """
            select id, title, company, seniority::text, min_years_experience,
                   jsonb_array_length(requirements) as requirements_count, created_at
            from public.job_descriptions where user_id = cast(:user_id as uuid)
            order by created_at desc limit 1
            """
        ),
        {"user_id": user_id},
    ).mappings().first()
    return dict(row) if row else None


def as_uuid(value: str) -> str:
    """Fail early on a malformed id instead of sending it to Postgres as a cast error."""
    return str(uuid_mod.UUID(value))


__all__ = [
    "EvidenceRequired",
    "UserUnresolved",
    "counts",
    "latest_jd",
    "latest_resume",
    "profile_payload",
    "resolve_user",
    "save_jd",
    "save_resume",
    "upsert_skills",
]
