"""The interview engine's honesty rules, as tests.

If these pass, a fluent answer with no example cannot mark a skill verified, and no
score can exist without a quote the candidate actually said.
"""
from app.interview import questions as engine

SKILL = {
    "skill_id": "content-strategy",
    "name": "Content Strategy",
    "category": "Content",
    "priority": 0.6,
    "priority_band": "critical",
    "status": "unverified",
    "verified_level": "beginner",
    "expected_level": "intermediate",
    "in_jd": True,
    "evidence": [{"type": "resume_project", "quote": "Built a 40-post editorial calendar"}],
}

EXPERT = (
    "On the club newsletter I ran a survey of 120 readers to pick angles instead of guessing. "
    "I wrote five hooks for each idea, tested two of them, and the winning hook doubled open "
    "rate from 22% to 41%. The trade-off was spending less time on the calendar and more on "
    "the first line."
)
FLUENT_EMPTY = (
    "Content strategy is something I care about deeply and I have followed the space for years. "
    "I read a lot about hooks and angles and how to write posts people finish. In general I "
    "believe the audience comes first and evidence matters, and I try to write posts that "
    "structure the word choice well and build a repeatable calendar."
)
VAGUE = "I think content strategy is important and I am good at it because I read about marketing."


def plan_for(skill=None):
    return engine.build_plan([skill or SKILL], total=1)


# ------------------------------------------------------------------- question design


def test_plan_is_ordered_by_priority_and_has_no_duplicates():
    skills = [
        {**SKILL, "skill_id": "low", "priority": 0.1},
        {**SKILL, "skill_id": "high", "priority": 0.9},
        {**SKILL, "skill_id": "high", "priority": 0.9},
        {**SKILL, "skill_id": "mid", "priority": 0.5},
    ]
    plan = engine.build_plan(skills, total=3)
    assert [q.skill_id for q in plan] == ["high", "mid", "low"]


def test_every_question_carries_a_rubric_from_the_taxonomy():
    question = plan_for()[0]
    assert question.rubric, "a question without a rubric cannot be scored honestly"
    assert all(item.terms for item in question.rubric)
    assert question.subtopic_id


def test_a_quoted_resume_project_asks_about_that_project():
    question = plan_for()[0]
    assert question.source == "resume_project"
    assert question.question_type == "project_deep_dive"
    assert "40-post editorial calendar" in question.text


def test_a_verified_skill_is_probed_harder_not_easier():
    question = plan_for({**SKILL, "status": "verified", "priority_band": "low"})[0]
    assert question.source == "verified_skill"
    assert question.question_type == "advanced"
    assert "wrong" in question.text


def test_without_a_quote_a_critical_gap_asks_for_an_example():
    skill = {**SKILL, "evidence": []}
    question = plan_for(skill)[0]
    assert question.source == "weak_skill"
    assert question.question_type == "fundamentals"
    assert "real example" in question.text


# ------------------------------------------------------------------------- scoring


def test_an_answer_with_numbers_and_outcomes_reaches_verified():
    result = engine.score_answer(plan_for()[0], EXPERT)
    assert result.score >= 0.75
    assert result.status_after == "verified"


def test_the_quote_is_verbatim_from_the_answer():
    result = engine.score_answer(plan_for()[0], EXPERT)
    assert result.quote is not None
    assert result.quote in EXPERT


def test_fluent_keyword_soup_cannot_be_verified():
    """The failure mode this product exists to prevent."""
    result = engine.score_answer(plan_for()[0], FLUENT_EMPTY)
    assert result.score <= 0.45
    assert result.status_after in ("weak", "needs_revision")
    assert "no_specifics" in result.flags


def test_a_vague_answer_scores_low_and_says_why():
    result = engine.score_answer(plan_for()[0], VAGUE)
    assert result.score < 0.4
    assert result.why


def test_an_empty_answer_is_evidence_free_not_a_zero_confidence_pass():
    result = engine.score_answer(plan_for()[0], "")
    assert result.score == 0.0
    assert result.quote is None
    assert result.status_after == "needs_revision"
    assert "empty" in result.flags


def test_a_score_never_exceeds_one():
    long_expert = " ".join([EXPERT] * 6)
    assert engine.score_answer(plan_for()[0], long_expert).score <= 1.0


def test_scoring_is_deterministic():
    question = plan_for()[0]
    first = engine.score_answer(question, EXPERT)
    second = engine.score_answer(question, EXPERT)
    assert first == second


def test_scores_are_labelled_with_who_scored_them():
    assert engine.score_answer(plan_for()[0], EXPERT).scored_by == "rubric"


def test_communication_never_claims_a_perfect_score():
    """Words on a page cannot prove delivery, so the transcript proxy is capped below 1."""
    from app.interview.service import _communication

    asked = [{"content": "q"}] * 3
    said = [{"content": " ".join(["word"] * 400)}] * 3
    score = _communication(asked, said)
    assert score == 0.92
    assert score < 1.0
