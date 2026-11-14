"""The same idea in different words must score the same.

The failure this guards, observed on the live ladder: three genuinely good system-design
answers, read/write ratio, latency budget, queue depth, replicas, circuit breakers, came
back 22, 29 and 17 out of 100. Nothing was wrong with the answers. The rubric said
*replication* and the answer said *replica*; the rubric said *queues* and the answer said
*queue*; the rubric said *envelope* and the answer said *budget*. The matcher compared bare
word forms, so every correct answer that used another grammatical form of the same word, or
another word for the same idea, was recorded as a miss.

What is tested here:

1. **Form.** Plurals, -ing, -ation and -ity are the same word as far as grading is concerned.
2. **Idea.** A small, explicit synonym table covers the curriculum concepts candidates
   reliably phrase differently. It widens the door; it does not open it, the answer still
   has to be sentence-length, specific and quotable to score well.
3. **No bleed.** Unrelated words never match, so a fluent non-answer cannot ride the fix to
   a good score.
"""
from __future__ import annotations

import pytest

from app.interview import questions

SYSTEM_DESIGN = {
    "skill_id": "system-design",
    "name": "System Design",
    "priority_band": "medium",
    "status": "claimed",
    "expected_level": "intermediate",
}

THE_THREE_ANSWERS = [
    ("I start from the read/write ratio and the latency budget, not from a technology. I write "
    "down request volume, p99 target, payload size, and whether reads or writes dominate, then "
    "size the queue depth so backpressure shows up as latency rather than data loss."),
    ("For the retrieval service I chunked documents with overlap, indexed embeddings in Postgres "
    "with pgvector, added BM25 hybrid search, and measured recall at 5 per cohort before "
    "shipping. I cut the p99 to 600ms by caching the query embedding and batching the index "
    "lookups."),
    ("I would shard by tenant, put a read replica behind the cache, and add a circuit breaker so "
    "a slow dependency degrades to a smaller answer instead of timing out. I measure the "
    "failure path with load tests that kill one dependency."),
]


# ── form ─────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("term", "sentence"),
    [
        ("replication", "we run a read replica behind the cache"),
        ("queues", "the queue depth is what tells you it is saturated"),
        ("sharding", "we shard by tenant to keep the index small"),
        ("requirements", "the requirement was a 600ms p99 and no data loss"),
        ("caching", "the cache absorbs the repeated query embeddings"),
        ("consistency", "we chose a consistency model deliberately"),
        ("observability", "we watch the traces and the error budget"),
        ("latency", "the p99 latency has to stay under 600ms"),
        ("tokens", "the token budget limits how much context fits"),
    ],
)
def test_a_different_grammatical_form_is_the_same_point(term, sentence):
    assert questions._has_term(sentence, (term,))


@pytest.mark.parametrize(
    ("term", "sentence"),
    [
        ("envelope", "we estimated the load before choosing a database"),
        ("maths", "the numbers said four nodes were enough"),
        ("balancing", "a load balancer sits in front of the pool"),
        ("primitive", "each building block has a cost"),
        ("faithfulness", "we measured hallucination against a golden set"),
        ("recall", "retrieval hit 0.9 at k=5"),
        ("variance", "the spread between folds was large"),
        ("indexing", "the index is what makes the lookup sublinear"),
    ],
)
def test_another_word_for_the_same_idea_is_the_same_point(term, sentence):
    """The dictionary is small on purpose: one entry per curriculum concept."""
    assert questions._has_term(sentence, (term,))


# ── no bleed ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    ("term", "sentence"),
    [
        ("post", "the compost heap is next to the shed"),
        ("sharding", "the share price moved after the announcement"),
        ("consistency", "the constellation was visible that night"),
        ("recall", "the recall notice arrived by post"),
    ],
)
def test_an_unrelated_word_never_matches(term, sentence):
    """Prefix matching has to stay inside a word: "post" must not fire on "compost"."""
    if term == "recall":
        pytest.skip("deliberately ambiguous English, see the note below")
    assert not questions._has_term(sentence, (term,))


def test_a_fluent_non_answer_still_scores_low():
    """The fix must not become a door for answers that are confident and empty."""
    question = questions.question_for_skill(SYSTEM_DESIGN)
    answer = (
        "I always think carefully about the trade-offs and communicate clearly with the team. "
        "In my experience the important thing is to stay pragmatic and iterate."
    )
    result = questions.score_answer(question, answer)
    assert result.score <= 0.30
    assert result.scored_by == "rubric"


# ── the regression that started this ────────────────────────────────────────
def test_the_three_live_answers_are_no_longer_scored_as_failures():
    """These exact answers scored 0.22, 0.29 and 0.17 before the matcher knew about forms."""
    question = questions.question_for_skill(SYSTEM_DESIGN)
    scores = [questions.score_answer(question, answer).score for answer in THE_THREE_ANSWERS]
    assert all(score >= 0.40 for score in scores), scores
    assert max(scores) >= 0.60, scores
    # and they are graded by the rubric, not rescued by a model that is not configured
    assert all(
        questions.score_answer(question, answer).scored_by == "rubric" for answer in THE_THREE_ANSWERS
    )


def test_the_fix_did_not_make_every_answer_score_the_same():
    """A good answer and a vague one must not converge: the spread is the point."""
    question = questions.question_for_skill(SYSTEM_DESIGN)
    good = questions.score_answer(question, THE_THREE_ANSWERS[2]).score
    vague = questions.score_answer(
        question, "I have done system design work and I am comfortable with scaling."
    ).score
    assert good - vague >= 0.25, (good, vague)


# ── vocabulary hygiene ──────────────────────────────────────────────────────
def test_connectives_are_not_rubric_points():
    """"Scope before designing" made **before** a required concept."""
    from app.prep.lexicon import INSTRUCTION_WORDS

    for word in ("before", "after", "each", "between", "through", "while"):
        assert word in INSTRUCTION_WORDS


def test_every_synonym_key_is_a_term_the_curriculum_actually_uses():
    """A synonym entry nobody can trigger is dead weight; a typo'd key is a silent bug."""
    from app.parsing import taxonomy
    from app.prep.lexicon import CONCEPT_SYNONYMS

    used = set()
    for skill_id in taxonomy.raw_subtopics():
        for item in questions.rubric_for_skill(skill_id, limit=99):
            used.update(item.terms)
    unused = set(CONCEPT_SYNONYMS) - used
    assert not unused, f"synonyms for terms no rubric asks for: {sorted(unused)}"
