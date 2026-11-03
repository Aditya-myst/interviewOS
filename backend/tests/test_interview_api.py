"""The interview loop over HTTP, in memory mode.

No database in tests, which is exactly the mode this exercises: sessions that work and
say they are not saved, rather than a 503.

The contract requires 3–12 questions per session, so the shortest real session is three
answers — tests play all three rather than inventing a one-question special case.
"""
from fastapi.testclient import TestClient

from app.main import create_app

ANSWER = (
    "On the club newsletter I ran a survey of 120 readers to pick angles instead of guessing. "
    "I wrote five hooks for each idea, tested two of them, and the winning hook doubled open "
    "rate from 22% to 41%."
)
MIN_QUESTIONS = 3


def client() -> TestClient:
    return TestClient(create_app())


def start(api: TestClient, questions: int = MIN_QUESTIONS) -> dict:
    response = api.post(
        "/v1/interview/start",
        json={"mode": "jd_based", "question_count": max(questions, MIN_QUESTIONS)},
    )
    assert response.status_code == 200, response.text
    return response.json()


def answer(api: TestClient, session_id: str, text: str = ANSWER) -> dict:
    response = api.post("/v1/interview/answer", json={"session_id": session_id, "answer": text})
    assert response.status_code == 200, response.text
    return response.json()


def play(api: TestClient, session_id: str, count: int = MIN_QUESTIONS) -> dict:
    body: dict = {}
    for _ in range(count):
        body = answer(api, session_id)
    return body


def test_starting_a_session_returns_a_question_from_the_priority_list():
    with client() as api:
        state = start(api)
        assert state["status"] == "active"
        assert state["asked"] == 0
        assert state["total"] == MIN_QUESTIONS
        assert state["question"]["text"]
        assert state["question"]["skill_id"]
        # source says where the question came from; question_type says what kind it is
        assert state["question"]["source"] in {
            "jd",
            "resume_project",
            "weak_skill",
            "verified_skill",
            "general",
        }
        assert state["question"]["question_type"] in {
            "fundamentals",
            "advanced",
            "coding",
            "debugging",
            "project_deep_dive",
            "scenario",
            "system_design",
            "behavioral",
        }


def test_a_session_shorter_than_the_contract_is_rejected():
    with client() as api:
        response = api.post("/v1/interview/start", json={"mode": "jd_based", "question_count": 1})
        assert response.status_code == 422


def test_memory_mode_is_declared_not_implied():
    with client() as api:
        response = api.post("/v1/interview/start", json={"mode": "jd_based"})
        assert response.headers["X-Data-Source"] in {"memory", "database"}
        assert response.headers.get("X-Fallback-Reason") in {"no_db", "no_profile", "no_rows", None}


def test_an_answer_returns_feedback_with_a_quote_and_moves_on():
    with client() as api:
        state = start(api)
        body = answer(api, state["session_id"])
        feedback = body["feedback"]
        assert 0.0 <= feedback["score"] <= 1.0
        assert feedback["scored_by"] == "rubric"
        assert feedback["quote"] is None or feedback["quote"] in ANSWER
        assert body["state"]["asked"] == 1
        assert body["report"] is None
        assert body["state"]["question"] is not None


def test_the_last_answer_closes_the_session_and_builds_the_report():
    with client() as api:
        state = start(api)
        body = play(api, state["session_id"])
        assert body["state"]["status"] == "completed"
        assert body["state"]["question"] is None
        report = body["report"]
        assert report["per_skill"]
        assert report["persisted"] is False
        # transcript-derived, and named that way in the payload
        assert "communication_transcript_based" in report["overall_scores"]
        assert report["scored_by"] == "rubric"


def test_the_report_can_be_read_back_after_the_session_ends():
    with client() as api:
        state = start(api)
        play(api, state["session_id"])
        response = api.get(f"/v1/interview/{state['session_id']}/report")
        assert response.status_code == 200
        assert response.json()["session_id"] == state["session_id"]


def test_evaluate_reproduces_the_same_report():
    """Scoring is a function of the transcript, so a reviewer can re-run it."""
    with client() as api:
        state = start(api)
        body = play(api, state["session_id"])
        again = api.post(f"/v1/interview/{state['session_id']}/evaluate")
        assert again.status_code == 200
        assert again.json()["overall_scores"]["overall"] == body["report"]["overall_scores"]["overall"]


def test_an_unknown_session_falls_back_to_the_recorded_report_and_says_so():
    with client() as api:
        response = api.get("/v1/interview/does-not-exist/report")
        assert response.status_code == 200
        assert response.headers["X-Data-Source"] == "fixture"
        assert response.headers["X-Fallback-Reason"] == "no_session"


def test_the_transcript_keeps_both_sides_verbatim():
    with client() as api:
        state = start(api)
        answer(api, state["session_id"])
        messages = api.get(f"/v1/interview/{state['session_id']}/transcript").json()["messages"]
        assert [m["role"] for m in messages] == ["interviewer", "candidate", "interviewer"]
        assert messages[1]["content"] == ANSWER


def test_answer_to_a_finished_session_is_a_conflict_not_a_second_score():
    with client() as api:
        state = start(api)
        play(api, state["session_id"])
        again = api.post(
            "/v1/interview/answer", json={"session_id": state["session_id"], "answer": ANSWER}
        )
        assert again.status_code == 409


def test_the_report_works_for_a_role_with_no_engineering_skills():
    """A content, design or education profile must get a full report.

    "Technical" used to be computed from Backend/Data/Infra/AI categories, so anyone
    preparing for a non-engineering role saw technical: null and an empty line where
    their domain score should be.
    """
    from app.interview import service

    marketing = [
        {"skill_id": "content-strategy", "name": "Content Strategy", "category": "Content",
         "priority": 0.57, "jd_importance": 0.95, "priority_band": "critical"},
        {"skill_id": "seo", "name": "SEO & Search", "category": "Marketing",
         "priority": 0.41, "jd_importance": 0.72, "priority_band": "high"},
        {"skill_id": "newsletter", "name": "Newsletter & Email", "category": "Growth",
         "priority": 0.14, "jd_importance": 0.86, "priority_band": "low"},
        {"skill_id": "visual-design", "name": "Visual Design", "category": "Design",
         "priority": 0.0, "jd_importance": 0.5, "priority_band": "low"},
    ]
    core = service.core_skill_ids(marketing)
    assert core == {"content-strategy", "newsletter", "seo"}  # the three the JD cares most about
    assert "visual-design" not in core
