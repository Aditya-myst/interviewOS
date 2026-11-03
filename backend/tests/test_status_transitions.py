"""The status table in `app/prep/status.py` mirrors the schema's trigger, and the schema
wins every argument.

The bug: an interview scoring 0.2 on a skill that was only ever `claimed` asked for
`needs_revision`. The trigger refused it (`illegal transition claimed -> needs_revision`)
and the exception escaped as a 500 *after* the candidate had answered — the turn was lost.

Two guarantees are tested here:
1. `reconcile` never returns a value the trigger would refuse (checked against a real
   database by attempting every pair, when one is available).
2. A bad answer never promotes a skill: a failed measurement either demotes it or leaves it
   alone.
"""
from __future__ import annotations

import os

import pytest

from app.prep.status import LEGAL, STATUSES, can_transition, reconcile

DSN = os.environ.get("INTERVIEWOS_TEST_DATABASE_URL")
USER = "11111111-1111-4111-8111-111111111111"
WANTED = ("weak", "developing", "verified", "needs_revision")


def test_the_table_covers_every_status():
    assert set(LEGAL) == set(STATUSES)
    for current, allowed in LEGAL.items():
        assert allowed <= set(STATUSES), f"{current} points at an unknown status"


@pytest.mark.parametrize("current", STATUSES)
@pytest.mark.parametrize("wanted", WANTED)
def test_reconcile_always_yields_a_legal_move(current, wanted):
    got = reconcile(current, wanted)
    assert can_transition(current, got), f"{current} -> {got} would be refused by the schema"


def test_a_failed_answer_never_promotes_a_skill():
    """The exact bug: 0.2 on a claimed skill must not become 'developing' or 'verified'."""
    assert reconcile("claimed", "needs_revision") == "weak"
    assert reconcile("unverified", "needs_revision") == "weak"
    assert reconcile("weak", "needs_revision") == "weak"
    # and a skill that needs revision does not drift upwards on a worse answer
    assert reconcile("needs_revision", "weak") == "needs_revision"


def test_a_verified_skill_never_slides_back_to_verified_looking_states():
    assert reconcile("verified", "weak") == "needs_revision"
    assert reconcile("verified", "developing") == "needs_revision"


def test_unknown_statuses_are_ignored_rather_than_written():
    assert reconcile("claimed", "expert") == "claimed"


@pytest.mark.skipif(not DSN, reason="set INTERVIEWOS_TEST_DATABASE_URL to run against Postgres")
def test_every_pair_is_accepted_by_the_real_trigger():
    """Walk the whole matrix against Postgres: the mirror must match the guard exactly."""
    from sqlalchemy import create_engine, text

    engine = create_engine(DSN)
    with engine.begin() as conn:
        conn.execute(
            text(
                "insert into auth.users (id, email) values (:u, 't@e.st') "
                "on conflict (id) do nothing"
            ),
            {"u": USER},
        )
        conn.execute(
            text(
                "insert into public.profiles (id, email, full_name) values (:u, 't@e.st', 'T') "
                "on conflict (id) do nothing"
            ),
            {"u": USER},
        )
        conn.execute(
            text(
                "insert into public.skills (id, name, category, aliases, interview_relevance) "
                "values ('content-strategy', 'Content Strategy', 'Marketing', '{}', 0.8) "
                "on conflict (id) do nothing"
            )
        )

    checked = 0
    for current in STATUSES:
        for wanted in WANTED:
            target = reconcile(current, wanted)
            with engine.begin() as conn:
                conn.execute(
                    text("delete from public.candidate_skills where user_id = cast(:u as uuid)"),
                    {"u": USER},
                )
                verified = "'beginner'::public.verified_level" if current in (
                    "verified",
                    "needs_revision",
                ) else "null"
                conn.execute(
                    text(
                        f"""
                        insert into public.candidate_skills
                          (user_id, skill_id, status, verified_level, expected_level, confidence,
                           jd_importance, interview_relevance, gap, priority, priority_band,
                           explanation, in_resume, in_jd, evidence)
                        values (cast(:u as uuid), 'content-strategy', cast(:cur as public.skill_status),
                                {verified}, 'expert', 0.5, 0.5, 0.5, 0.5, 0.5, 'medium', 'seeded',
                                true, true, '[{{"type":"assessment_answer","quote":"q"}}]'::jsonb)
                        """
                    ),
                    {"u": USER, "cur": current},
                )
            # the write that used to raise; a verified row also needs a level, which the
            # interview write-back supplies from the rung it just scored
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "update public.candidate_skills set status = cast(:s as public.skill_status), "
                        "verified_level = case when :s = 'verified' "
                        "then coalesce(verified_level, 'beginner'::public.verified_level) "
                        "else verified_level end "
                        "where user_id = cast(:u as uuid)"
                    ),
                    {"u": USER, "s": target},
                )
            checked += 1
    assert checked == len(STATUSES) * len(WANTED)
