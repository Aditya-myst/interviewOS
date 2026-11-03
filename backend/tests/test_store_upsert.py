"""The upsert must not be able to un-verify a skill.

The bug this file exists for: `on conflict do update set status = excluded.status` made
every resume re-upload reset a graded skill to `unverified`. The schema's transition guard
refused the downgrade (`illegal transition weak -> unverified`) and the upload died with a
500 — a crash caused by the storage layer overwriting state it did not own.

Two layers of protection, because the SQL text test runs everywhere and the database test
only runs where there is a database:

1. `test_upsert_never_writes_status` — the statement has no `status =` assignment in its
   conflict branch, so no future edit can reintroduce it silently.
2. `test_upsert_preserves_verification_against_a_real_database` — the whole thing against
   Postgres, including the trigger, the evidence history and the null-preserving coalesce.
   Skipped unless INTERVIEWOS_TEST_DATABASE_URL points at a database with docs/sql applied.
"""
from __future__ import annotations

import json
import os

import pytest

from app import store
from app.prep.priority import ScoredSkill

DSN = os.environ.get("INTERVIEWOS_TEST_DATABASE_URL")
USER = "11111111-1111-4111-8111-111111111111"


def _row(**overrides) -> ScoredSkill:
    base = {
        "skill_id": "content-strategy",
        "name": "Content Strategy",
        "category": "Marketing",
        "status": "unverified",
        "claimed_level": None,
        "verified_level": None,
        "expected_level": "expert",
        "confidence": 0.0,
        "jd_importance": 0.95,
        "interview_relevance": 0.85,
        "gap": 0.95,
        "priority": 0.767,
        "priority_band": "critical",
        "explanation": "required in the JD, absent from the resume",
        "in_resume": False,
        "in_jd": True,
        "evidence": [{"type": "jd_requirement", "quote": "2+ years of content strategy"}],
    }
    base.update(overrides)
    return ScoredSkill(**base)


def test_upsert_never_writes_status():
    """The regression, as text: no assignment to `status` after `on conflict`."""
    conflict = str(store.UPSERT_SKILL).split("on conflict", 1)[1]
    assignments = [
        line.split("=", 1)[0].strip()
        for line in conflict.splitlines()
        if "=" in line and not line.strip().startswith("--")
    ]
    assert "status" not in assignments, (
        "the conflict branch must not assign status — that is what crashed the upload"
    )
    assert "verified_level" in assignments


def test_upsert_keeps_evidence_append_only():
    sql = str(store.UPSERT_SKILL).lower()
    assert "jsonb_array_elements" in sql, "evidence must merge, not be replaced"
    assert "coalesce(excluded.verified_level" in sql, "a null verified_level must not erase one"
    assert "coalesce(excluded.claimed_level" in sql


@pytest.mark.skipif(not DSN, reason="set INTERVIEWOS_TEST_DATABASE_URL to run against Postgres")
def test_upsert_preserves_verification_against_a_real_database():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    engine = create_engine(DSN)
    with engine.begin() as conn:
        conn.execute(
            text(
                "insert into auth.users (id, email) values (:u, 'test@example.com') "
                "on conflict (id) do nothing"
            ),
            {"u": USER},
        )
        conn.execute(
            text(
                "insert into public.profiles (id, email, full_name) values (:u, 'test@example.com', 'Test') "
                "on conflict (id) do nothing"
            ),
            {"u": USER},
        )
        conn.execute(
            text(
                "insert into public.skills (id, name, category, aliases, interview_relevance) "
                "values ('content-strategy', 'Content Strategy', 'Marketing', '{}', 0.85) "
                "on conflict (id) do nothing"
            )
        )
        conn.execute(
            text("delete from public.candidate_skills where user_id = cast(:u as uuid)"),
            {"u": USER},
        )
        # the state that made the upload explode: an interview already graded it weak
        conn.execute(
            text(
                """
                insert into public.candidate_skills
                  (user_id, skill_id, status, verified_level, expected_level, confidence,
                   jd_importance, interview_relevance, gap, priority, priority_band,
                   explanation, in_resume, in_jd, evidence)
                values
                  (cast(:u as uuid), 'content-strategy', 'weak', 'beginner', 'expert', 0.4,
                   0.9, 0.85, 0.6, 0.5, 'high', 'graded by an interview', true, true,
                   '[{"type":"assessment_answer","quote":"I ran one reader survey"}]'::jsonb)
                """
            ),
            {"u": USER},
        )

    # the upload's recompute: unverified, no verified level, JD-only evidence
    with Session(engine) as session:
        written = store.upsert_skills(session, user_id=USER, rows=[_row()])
        session.commit()
    assert written == 1

    with engine.connect() as conn:
        status, verified, evidence, priority = conn.execute(
            text(
                "select status::text, verified_level::text, evidence, priority "
                "from public.candidate_skills where user_id = cast(:u as uuid) "
                "and skill_id = 'content-strategy'"
            ),
            {"u": USER},
        ).one()

    assert status == "weak", "a resume re-upload must not un-verify a graded skill"
    assert verified == "beginner", "the verified level was overwritten with null"
    items = json.loads(evidence) if isinstance(evidence, str) else evidence
    types = [item["type"] for item in items]
    assert "assessment_answer" in types, "the interview quote was deleted by the recompute"
    assert "jd_requirement" in types, "the new JD quote was not added"
    assert float(priority) > 0.7, "scores still update — only the verification state is frozen"


def test_prune_never_touches_a_graded_row():
    """Stale rows go; earned ones stay. The SQL is the contract here."""
    sql = str(store.PRUNE_STALE).lower()
    assert "status in ('claimed', 'unverified')" in sql
    for graded in ("weak", "developing", "verified", "needs_revision"):
        assert f"'{graded}'" not in sql, f"pruning must not delete {graded} rows"
    assert "skill_id <> all(:keep)" in sql


def test_prune_refuses_an_empty_keep_list():
    class Exploding:
        def execute(self, *a, **k):
            raise AssertionError("an empty keep list must not reach the database")

    assert store.prune_stale_skills(Exploding(), user_id="u", keep=[]) == 0


@pytest.mark.skipif(not DSN, reason="set INTERVIEWOS_TEST_DATABASE_URL to run against Postgres")
def test_prune_against_a_real_database():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    engine = create_engine(DSN)
    with engine.begin() as conn:
        conn.execute(
            text(
                "insert into public.skills (id, name, category, aliases, interview_relevance) "
                "values ('docker', 'Docker', 'Infra', '{}', 0.7) on conflict (id) do nothing"
            )
        )
        conn.execute(
            text("delete from public.candidate_skills where user_id = cast(:u as uuid)"),
            {"u": USER},
        )
        # content-strategy: graded, and still mentioned → must survive
        # docker: never graded, no longer mentioned → stale, must go
        for skill, status in (("content-strategy", "verified"), ("docker", "unverified")):
            conn.execute(
                text(
                    """
                    insert into public.candidate_skills
                      (user_id, skill_id, status, verified_level, expected_level, confidence,
                       jd_importance, interview_relevance, gap, priority, priority_band,
                       explanation, in_resume, in_jd, evidence)
                    values (cast(:u as uuid), :s, cast(:st as public.skill_status),
                            case when :st = 'verified' then 'beginner'::public.verified_level end,
                            'expert', 0.5, 0.5, 0.5, 0.5, 0.5, 'medium', 'seeded', true, true,
                            '[{"type":"assessment_answer","quote":"I graded this"}]'::jsonb)
                    """.replace("'expert',", "'expert',").replace(
                        ":st as public.skill_status), 'expert'",
                        ":st as public.skill_status), 'expert'",
                    ) + """
                    """
                ),
                {"u": USER, "s": skill, "st": status},
            )

    with Session(engine) as session:
        pruned = store.prune_stale_skills(session, user_id=USER, keep=["content-strategy"])
        session.commit()
    assert pruned == 1, "only the ungraded stale row should be removed"

    with engine.connect() as conn:
        left = {
            row[0]
            for row in conn.execute(
                text(
                    "select skill_id from public.candidate_skills where user_id = cast(:u as uuid)"
                ),
                {"u": USER},
            )
        }
    assert left == {"content-strategy"}, (
        "the ungraded stale row goes and the graded one stays"
    )
