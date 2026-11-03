"""Dashboard and roadmap, computed from rows.

The interesting properties are not "does it return 200" but: is readiness a number
with a definition, does a missing resource show up as a gap instead of a blank card,
and can the same input produce a different answer on a second run.
"""
from datetime import date

import pytest

from app.parsing import jd as jd_mod
from app.parsing import resume as resume_mod
from app.parsing.extract import extract
from app.prep import priority
from app.prep.dashboard import attainment, build_dashboard, coverage, readiness, readiness_label
from app.prep.roadmap import build_roadmap

from .test_planning import JD_TEXT, RESUME_TEXT  # reuse the same synthetic pair

# Relative on purpose: an absolute `tests.` import can be hijacked by any installed
# distribution that ships a `tests` package (bitcoinlib does). See tests/__init__.py.


def scored_rows(verified: dict | None = None):
    resume = resume_mod.parse(extract("resume.txt", RESUME_TEXT.encode()))
    jd = jd_mod.parse(JD_TEXT)
    return priority.score(resume, jd, verified=verified)


# ── readiness ────────────────────────────────────────────────────────────────
def test_attainment_is_a_ratio_of_levels_not_a_mood():
    assert attainment(held="advanced", expected="advanced") == 1.0
    assert attainment(held="none", expected="expert") == 0.0
    assert attainment(held="listed", expected="advanced") == pytest.approx(0.25 / 0.75, rel=1e-3)
    # never above 1: exceeding the JD's bar does not make you more ready than ready
    assert attainment(held="expert", expected="beginner") == 1.0


def test_readiness_weights_by_what_the_jd_asked_for():
    rows = scored_rows()
    value = readiness(rows)
    assert 0 <= value <= 100
    # a JD-only skill contributes zero attainment and still pulls the average down
    assert value < 100


def test_readiness_labels_are_thresholds_in_one_place():
    assert readiness_label(0) == "not_ready"
    assert readiness_label(24.9) == "not_ready"
    assert readiness_label(25) == "early"
    assert readiness_label(50) == "approaching"
    assert readiness_label(75) == "interview_ready"


def test_a_verified_skill_raises_readiness():
    base = readiness(scored_rows())
    better = readiness(scored_rows({"llm-rag": {"level": "expert", "evidence": []}}))
    assert better > base


# ── the dashboard payload ────────────────────────────────────────────────────
def test_history_is_as_long_as_the_measurements_we_have():
    """Exactly one point, because one measurement exists. A seven-day curve would
    have been the most tempting lie on the screen."""
    payload = build_dashboard(scored_rows(), target_role="AI Engineer", today=date(2026, 11, 2))
    assert payload["readiness_history"] == [{"date": "2026-11-02", "readiness": payload["readiness"]}]
    assert "not backfilled" in payload["history_basis"]


def test_an_empty_profile_has_no_history_at_all():
    payload = build_dashboard([], target_role=None)
    assert payload["readiness_history"] == []
    assert payload["readiness"] == 0
    assert payload["readiness_label"] == "not_ready"
    assert payload["stats"]["skills_total"] == 0


def test_dashboard_keys_match_the_shape_the_ui_reads():
    payload = build_dashboard(scored_rows(), target_role="AI Engineer")
    assert set(payload) >= {
        "readiness", "readiness_label", "provisional", "target_role",
        "readiness_history", "stats", "coverage", "priority_skills", "interviews",
    }
    assert payload["provisional"] is True          # no assessment yet
    assert len(payload["priority_skills"]) == 3    # the top three only
    assert payload["stats"]["verified_skills"] == 0


def test_coverage_counts_every_skill_exactly_once():
    rows = scored_rows()
    buckets = coverage(rows)
    total = sum(b["verified"] + b["developing"] + b["unverified"] for b in buckets)
    assert total == len(rows)


def test_interviews_and_average_score_come_from_rows_not_from_thin_air():
    payload = build_dashboard(
        scored_rows(),
        target_role="AI Engineer",
        interviews=[{"session_id": "a", "score": 50}, {"session_id": "b", "score": 70}],
    )
    assert payload["stats"]["mock_interviews"] == 2
    assert payload["stats"]["avg_interview_score"] == 60.0


# ── the roadmap ──────────────────────────────────────────────────────────────
CATALOGUE = {
    ("llm-rag", "rag-evaluation"): [
        {"id": "1", "title": "Ragas docs", "url": "https://docs.ragas.io/", "provider": "Ragas",
         "kind": "docs", "is_paid": False, "license": "Apache-2.0", "verified_at": None},
        {"id": "2", "title": "Ragas get started", "url": "https://docs.ragas.io/x/",
         "provider": "Ragas", "kind": "exercise", "is_paid": False, "license": "Apache-2.0",
         "verified_at": None},
    ],
}


def test_topics_come_from_the_taxonomy_never_from_the_model():
    from app.parsing import taxonomy

    roadmap = build_roadmap(scored_rows(), CATALOGUE, target_role="AI Engineer")
    assert roadmap["topics"], "expected at least one topic"
    known = {sub["title"] for subs in taxonomy.raw_subtopics().values() for sub in subs}
    for topic in roadmap["topics"]:
        assert topic["title"] in known


def test_a_missing_resource_is_a_named_gap_not_an_empty_card():
    roadmap = build_roadmap(scored_rows(), {}, target_role="AI Engineer")
    assert roadmap["topics"]
    for topic in roadmap["topics"]:
        assert topic["resources"] == []
        assert topic["missing_roles"] == ["concept", "practice", "checkpoint"]
    assert "lack a full set of resources" in roadmap["summary"]


def test_catalogue_rows_fill_roles_and_shrink_the_gap_list():
    roadmap = build_roadmap(scored_rows(), CATALOGUE, target_role="AI Engineer")
    filled = [t for t in roadmap["topics"] if t["resources"]]
    if filled:  # depends on which subtopic the ordering picked
        topic = filled[0]
        roles = [r["role"] for r in topic["resources"]]
        assert roles[0] == "concept"
        assert "concept" not in topic["missing_roles"]


def test_the_roadmap_is_the_same_plan_every_time():
    first = build_roadmap(scored_rows(), CATALOGUE, target_role="AI Engineer")
    second = build_roadmap(scored_rows(), CATALOGUE, target_role="AI Engineer")
    assert first == second
    assert [t["id"] for t in first["topics"]] == [t["id"] for t in second["topics"]]


def test_topics_are_ordered_by_priority_and_capped():
    roadmap = build_roadmap(scored_rows(), CATALOGUE, target_role="AI Engineer", limit=4)
    assert len(roadmap["topics"]) <= 4
    priorities = [t["priority"] for t in roadmap["topics"]]
    assert priorities == sorted(priorities, reverse=True)
    assert [t["order_index"] for t in roadmap["topics"]] == list(range(len(roadmap["topics"])))


def test_the_resource_query_types_its_array_parameter():
    """A list bound into `= any(...)` is only safe with an explicit cast.

    Without it Postgres has to infer the parameter type from context; when that
    inference fails the endpoint 500s, and the UI can only report "the API did not
    answer" — which reads like an outage, not a bug in one query.
    """
    from app import store

    sql = str(store.RESOURCES_SQL)
    assert "cast(:skill_ids as text[])" in sql
    assert "is_dead = false" in sql
