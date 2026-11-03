"""The roadmap may only plan for skills this posting involves.

The bug: after switching from a marketing resume to a backend one, the plan still opened
with newsletter and social-growth topics. The stale row was *supposed* to survive — it holds
a graded status and real evidence — but it kept the previous posting's `jd_importance` and
`priority`, so it outranked every skill the new documents actually mention.

Two defences, tested here and in `test_store_upsert.py`:

1. `build_roadmap` skips rows that are neither in the resume nor in the posting.
2. `store.prune_stale_skills` retires such rows: status/level/evidence kept, JD fields zeroed.
"""
from __future__ import annotations

from app.prep.priority import ScoredSkill
from app.prep.roadmap import build_roadmap


def row(skill_id: str, *, name: str, band: str, priority_value: float, in_resume: bool,
        in_jd: bool, status: str = "unverified", gap: float = 0.8) -> ScoredSkill:
    return ScoredSkill(
        skill_id=skill_id,
        name=name,
        category="Test",
        status=status,
        claimed_level=None,
        verified_level="beginner" if status == "verified" else None,
        expected_level="advanced",
        confidence=0.5,
        jd_importance=0.9 if in_jd else 0.0,
        interview_relevance=0.9,
        gap=gap,
        priority=priority_value,
        priority_band=band,
        explanation="seeded",
        in_resume=in_resume,
        in_jd=in_jd,
        evidence=[{"type": "resume_project", "quote": "did the thing"}],
    )


def test_a_stale_graded_skill_is_not_taught():
    """The exact symptom: a graded marketing row outranking the current backend work."""
    rows = [
        row("newsletter", name="Newsletter & Email", band="critical", priority_value=0.88,
            in_resume=False, in_jd=False, status="weak"),
        row("python", name="Python", band="high", priority_value=0.61, in_resume=True, in_jd=True),
    ]
    plan = build_roadmap(rows, {}, target_role="Backend Engineer")
    skills = {topic["skill_id"] for topic in plan["topics"]}
    assert "newsletter" not in skills, "a skill this posting never mentions must not be planned"
    assert "python" in skills


def test_a_skill_only_the_posting_asks_for_is_still_taught():
    """Not on the resume but required by the JD is the whole point of the product."""
    rows = [row("docker", name="Docker", band="critical", priority_value=0.7, in_resume=False, in_jd=True)]
    plan = build_roadmap(rows, {}, target_role="Backend Engineer")
    assert {t["skill_id"] for t in plan["topics"]} == {"docker"}


def test_the_plan_is_empty_when_nothing_is_related():
    rows = [
        row("seo", name="SEO & Search", band="critical", priority_value=0.9,
            in_resume=False, in_jd=False, status="weak"),
    ]
    plan = build_roadmap(rows, {}, target_role="Backend Engineer")
    assert plan["topics"] == []


def test_rows_without_the_flags_are_not_dropped():
    """`build_roadmap` is also called with plainer objects; absence of a flag is not a no."""
    class Plain:
        skill_id = "python"
        name = "Python"
        priority_band = "high"
        priority = 0.6
        gap = 0.7
        verified_level = None
        claimed_level = None
        explanation = "seeded"

    plan = build_roadmap([Plain()], {}, target_role=None)
    assert [t["skill_id"] for t in plan["topics"]]
