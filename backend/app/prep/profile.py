"""Scored rows → the SkillProfile payload the frontend already renders.

The shape is fixed by contracts/types.ts and by contracts/fixtures/skill_profile.json,
which the UI has been reading since Phase 3. Emitting the same keys from the pipeline
is what lets the frontend switch from fixture to database without a component change.
"""
from __future__ import annotations

from app.prep.priority import ScoredSkill

BAND_KEYS = ("critical", "high", "medium", "low")

# The profile contract buckets each skill three ways. A resume claim is *developing*
# evidence: something is there, nothing has been checked yet.
COVERAGE_BUCKET = {"verified": "verified", "claimed": "developing", "unverified": "unverified"}


def counts(rows: list[ScoredSkill]) -> dict[str, int]:
    tally = {key: 0 for key in BAND_KEYS}
    for row in rows:
        tally[row.priority_band] = tally.get(row.priority_band, 0) + 1
    tally["verified"] = sum(1 for row in rows if row.status == "verified")
    tally["unverified"] = sum(1 for row in rows if row.status == "unverified")
    return tally


def coverage_by_category(rows: list[ScoredSkill]) -> list[dict]:
    buckets: dict[str, dict[str, int]] = {}
    for row in rows:
        entry = buckets.setdefault(row.category, {"verified": 0, "developing": 0, "unverified": 0})
        entry[COVERAGE_BUCKET.get(row.status, "unverified")] += 1
    return [
        {"category": category, **values}
        for category, values in sorted(buckets.items(), key=lambda item: (-sum(item[1].values()), item[0]))
    ]


def build_profile(rows: list[ScoredSkill], *, provisional: bool = True) -> dict:
    """`provisional` is true until an assessment exists — a resume score is a hypothesis,
    and the UI says so."""
    return {
        "provisional": provisional,
        "counts": counts(rows),
        "coverage_by_category": coverage_by_category(rows),
        "skills": [row.as_json() for row in rows],
    }
