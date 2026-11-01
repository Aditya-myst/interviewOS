from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_matches_contract_shape():
    r = client.get("/v1/analytics/dashboard")
    assert r.status_code == 200
    assert r.headers["x-data-source"] == "fixture"
    body = r.json()
    assert {"readiness", "stats", "coverage", "priority_skills", "interviews"}.issubset(body)
    assert len(body["readiness_history"]) == 7
    assert body["readiness_history"][-1]["readiness"] == body["readiness"]


def test_dashboard_empty_state_is_a_real_payload():
    body = client.get("/v1/analytics/dashboard", params={"state": "empty"}).json()
    assert body["readiness"] == 0
    assert body["priority_skills"] == []
    assert body["coverage"] == []
    assert body["stats"]["skills_total"] == 0


def test_skills_profile_counts_add_up():
    body = client.get("/v1/skills/profile").json()
    counts = body["counts"]
    assert len(body["skills"]) == 9
    assert sum(counts[b] for b in ("critical", "high", "medium", "low")) == 9
    # every skill with an assessed status must carry evidence — the same rule
    # the database trigger enforces
    for skill in body["skills"]:
        if skill["status"] in ("weak", "developing", "verified"):
            assert skill["evidence"], f"{skill['skill_id']} claims {skill['status']} with no evidence"


def test_roadmap_topics_have_three_roles_or_an_honest_gap():
    body = client.get("/v1/learning/roadmap").json()
    assert len(body["topics"]) == 5
    for topic in body["topics"]:
        roles = {r["role"] for r in topic["resources"]}
        assert roles <= {"concept", "practice", "checkpoint"}
        assert "concept" in roles and "practice" in roles
        for res in topic["resources"]:
            assert res["url"].startswith("http")


def test_unknown_endpoint_is_a_404_not_a_crash():
    assert client.get("/v1/nope").status_code == 404
