"""`/v1/preparation/latest` must describe the candidate in the database.

It was the last read endpoint that never queried the store: with 23 live skill rows it still
returned a fixture plan for a different person. The header said `fixture`, which is honest,
but the screen above it was wrong — the exact defect the user asked to be rid of.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_preparation_serves_fixtures_and_says_so_without_a_database(client):
    response = client.get("/v1/preparation/latest")
    assert response.status_code == 200
    assert response.headers["x-data-source"] == "fixture"
    body = response.json()
    assert {"readiness", "next_best_action", "skill_profile", "roadmap"} <= set(body)
    assert response.headers.get("x-fallback-reason")


def test_preparation_goes_through_the_store(client, monkeypatch):
    """With rows available it must report `database`, and the plan must come from them."""
    from app.api import prep

    payload = {
        "id": "plan-1",
        "readiness": 51.1,
        "readiness_label": "approaching",
        "next_best_action": "RAG architecture end to end (LLM & RAG) — Describe ingest, retrieve, rerank, generate.",
        "generated_at": "2026-11-03T00:00:00Z",
        "parse_status": "ok",
        "skill_profile": {"provisional": True, "counts": {}, "coverage_by_category": [], "skills": []},
        "roadmap": {"id": "r1", "status": "active", "target_role": None, "summary": "s", "progress": {}, "topics": []},
    }
    monkeypatch.setattr(prep, "_from_store", lambda builder: (payload, None))
    response = client.get("/v1/preparation/latest")
    assert response.status_code == 200
    assert response.headers["x-data-source"] == "database"
    assert response.json()["readiness"] == 51.1
    assert "RAG architecture" in response.json()["next_best_action"]


def test_the_plan_is_stored_when_rows_exist(client, monkeypatch):
    """The stored path is a composition of the other three payloads — same candidate."""
    from app import store

    dashboard = {
        "readiness": 61.0,
        "readiness_label": "approaching",
        "provisional": True,
        "target_role": {"title": "AI Engineer"},
        "readiness_history": [],
        "history_basis": "seeded",
        "stats": {},
        "coverage": [],
        "priority_skills": [],
        "interviews": [],
    }
    profile = {"provisional": True, "counts": {"critical": 1}, "coverage_by_category": [], "skills": []}
    roadmap = {
        "id": "roadmap-1",
        "status": "active",
        "target_role": None,
        "summary": "1 topic",
        "progress": {},
        "topics": [
            {
                "id": "t1",
                "skill_id": "llm-rag",
                "skill_name": "LLM & RAG",
                "title": "RAG architecture end to end",
                "objective": "Describe ingest, retrieve, rerank, generate.",
                "status": "not_started",
            }
        ],
    }
    monkeypatch.setattr(store, "dashboard_payload", lambda *_a, **_k: dashboard)
    monkeypatch.setattr(store, "profile_payload", lambda *_a, **_k: profile)
    monkeypatch.setattr(store, "roadmap_payload", lambda *_a, **_k: roadmap)

    payload = store.preparation_payload(object(), user_id="u1")
    assert payload is not None
    assert payload["readiness"] == 61.0
    assert payload["skill_profile"] is profile
    assert payload["roadmap"] is roadmap
    assert payload["next_best_action"].startswith("RAG architecture end to end")


def test_the_plan_is_none_when_nothing_is_scored(monkeypatch):
    """None — not an empty plan — so the caller falls back and the header tells the truth."""
    from app import store

    monkeypatch.setattr(store, "dashboard_payload", lambda *_a, **_k: None)
    monkeypatch.setattr(store, "profile_payload", lambda *_a, **_k: None)
    monkeypatch.setattr(store, "roadmap_payload", lambda *_a, **_k: None)
    assert store.preparation_payload(object(), user_id="u1") is None
