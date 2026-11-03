"""Rubrics must ask for concepts, not for the syllabus's own instructions.

The failure this guards: the LLM-basics checkpoint wanted the terms "explain", "without",
"mysticism", "work" and the whole phrase "how llms work: tokens, context, temperature".
A candidate who explained tokens, context windows and temperature perfectly scored 22/100
because they never said "mysticism". Scores that thin are not "honest", they are noise.
"""
from __future__ import annotations

import pytest

from app.assessment.ladder import _objective_items
from app.interview import questions
from app.parsing import taxonomy
from app.prep.lexicon import INSTRUCTION_WORDS


def _all_subtopics():
    for skill_id, subs in taxonomy.raw_subtopics().items():
        for sub in subs:
            yield skill_id, sub


@pytest.mark.parametrize("skill_id", sorted(taxonomy.raw_subtopics()))
def test_no_rubric_term_is_an_instruction_word(skill_id):
    for item in questions.rubric_for_skill(skill_id, limit=99):
        for term in item.terms:
            assert term not in INSTRUCTION_WORDS, f"{skill_id}: rubric demands {term!r}"
            assert " " not in term, f"{skill_id}: {term!r} is a phrase no answer contains"


def test_every_subtopic_has_at_least_two_reachable_rubric_points():
    """A rubric with no reachable term scores every answer zero."""
    for skill_id, sub in _all_subtopics():
        assert len(_objective_items(sub)) >= 2, f"{skill_id}/{sub['id']} has no rubric"


def test_a_competent_answer_scores_like_a_competent_answer():
    """Explain LLM basics properly — in words a person would use — and be scored for it."""
    sub = next(s for s in taxonomy.raw_subtopics()["llm-rag"] if s["id"] == "llm-basics")
    rubric = _objective_items(sub)
    answer = (
        "An LLM predicts the next token, so the work is really in the tokens and the context "
        "you give it. The context window is the budget of tokens it can attend to at once, and "
        "past that the earliest text is simply dropped, which is why long documents get lossy. "
        "Temperature scales the logits before sampling: near zero the generation is repeatable "
        "and good for extraction, higher and it wanders. The limits follow from that: no "
        "retrieval, no memory beyond the window, and confident phrasing on things it never saw."
    )
    lowered = answer.lower()
    matched = [item for item in rubric if any(t in lowered for t in item.terms)]
    coverage = len(matched) / len(rubric)
    assert coverage >= 0.66, f"only {coverage:.0%} of {[i.terms for i in rubric]} recognised"


def test_a_vacuous_answer_does_not():
    sub = next(s for s in taxonomy.raw_subtopics()["llm-rag"] if s["id"] == "llm-basics")
    rubric = _objective_items(sub)
    vacuous = "I have used it a lot and I am a fast learner, so I would figure it out on the job."
    lowered = vacuous.lower()
    matched = [item for item in rubric if any(t in lowered for t in item.terms)]
    assert len(matched) <= 1, "an empty answer must not clear the rubric"
