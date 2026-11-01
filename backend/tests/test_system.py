from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_is_liveness_only():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["mode"] == "fixture"  # no DATABASE_URL in tests


def test_ready_reports_degraded_rather_than_failing():
    r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "degraded"          # no LLM keys, no database
    assert body["checks"]["database"]["state"] == "unconfigured"
    assert body["checks"]["llm"]["state"] == "unconfigured"
    assert body["checks"]["fixtures"]["ok"] is True


def test_llm_probe_says_why_nothing_answered():
    r = client.post("/dev/llm", json={"prompt": "say hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "llm_unavailable"
    assert body["configured"] == []
