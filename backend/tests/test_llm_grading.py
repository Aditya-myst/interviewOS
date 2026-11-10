"""The semantic pass must be able to help and must never be able to hurt.

The rubric matcher is literal: an answer that explains token budgets without saying the word
"limits" loses a point. An LLM fixes that. It also opens three new failure modes, and each
one is tested here:

- **It says 100 for a vacuous answer.** A verdict that disagrees with the deterministic score
  by more than MAX_DISAGREEMENT is discarded, and the rubric score stands.
- **It goes down / answers with prose.** No key, an outage, invalid JSON, half the rubric
  accounted for — every one of those returns None and the rubric stands untouched.
- **It is on by default.** It is not: without a key and without LLM_SCORING, no call is made
  at all.

The deterministic floors (no quote -> 0.25 ceiling, too short -> 0.15) are applied before the
model is consulted, so a silver tongue cannot buy credit for an answer with nothing in it.
"""
from __future__ import annotations

import json

from app.interview import questions
from app.llm import grading
from app.llm.cache import MemoryCache
from app.llm.gateway import Gateway


class FakeProvider:
    def __init__(self, payload: str, *, fail: bool = False):
        self.name = "fake"
        self.model = "fake-1"
        self.payload = payload
        self.fail = fail
        self.calls = 0

    def available(self) -> bool:
        return True

    def complete(self, prompt, *, system=None, json_mode=False):
        self.calls += 1
        if self.fail:
            raise RuntimeError("upstream 500")
        return self.payload


QUESTION = questions.Question(
    text="LLM & RAG — How LLMs work: tokens, context, temperature.",
    question_type="scenario",
    skill_id="llm-rag",
    skill_name="LLM & RAG",
    source="jd",
    rubric=(
        questions.RubricItem(key="tokens", terms=("tokens",)),
        questions.RubricItem(key="context", terms=("context",)),
        questions.RubricItem(key="limits", terms=("limits",)),
    ),
)

# Deliberately avoids the word "limits" while explaining it — the case the rubric punishes
# and a model should recognise.
ANSWER = (
    "A model can only attend to so much at once, so long documents get truncated and the "
    "middle is lost. I chunked with overlap and measured recall at 5 per cohort to catch it."
)


def _install(monkeypatch, provider, *, scoring=True):
    gw = Gateway(chain=[provider], cache=MemoryCache(), schema_version=1)
    monkeypatch.setattr("app.llm.get_gateway", lambda: gw)
    monkeypatch.setattr("app.llm.grading.get_gateway", lambda: gw, raising=False)
    monkeypatch.setattr(
        grading, "enabled", lambda: scoring and bool(provider.available())
    )


QUOTE = "I chunked with overlap and measured recall at 5 per cohort to catch it."


def _verdict(score: int, matched, missing, quote=QUOTE, rationale="Meaning matched, word missing."):
    return json.dumps(
        {
            "score": score,
            "matched": matched,
            "missing": missing,
            "quote": quote,
            "rationale": rationale,
        }
    )


def test_off_by_default_touches_no_provider(monkeypatch):
    provider = FakeProvider(_verdict(70, ["tokens", "context", "limits"], []))
    gw = Gateway(chain=[provider], cache=MemoryCache(), schema_version=1)
    monkeypatch.setattr("app.llm.get_gateway", lambda: gw)

    result = questions.score_answer(QUESTION, ANSWER)

    assert result.scored_by == "rubric"
    assert provider.calls == 0, "a model was called with LLM_SCORING off"


def test_the_vocabulary_gap_is_what_this_pass_closes(monkeypatch):
    """ANSWER explains the limits of a context window without ever saying "limits"."""
    baseline = questions.score_answer(QUESTION, ANSWER)
    assert baseline.scored_by == "rubric"
    assert baseline.quote is None, "the literal matcher found nothing quotable — the whole point"

    provider = FakeProvider(_verdict(70, ["tokens", "context", "limits"], []))
    _install(monkeypatch, provider, scoring=True)
    result = questions.score_answer(QUESTION, ANSWER)

    assert provider.calls == 1
    assert result.scored_by == "llm"
    assert result.score > baseline.score
    assert result.matched == ("tokens", "context", "limits")
    assert result.quote == QUOTE
    assert "llm_graded" in result.flags


def test_a_paraphrased_quote_throws_the_verdict_away(monkeypatch):
    """The model may not invent the evidence it is scored on."""
    provider = FakeProvider(
        _verdict(70, ["tokens", "context", "limits"], [], quote="I measured recall per cohort.")
    )
    _install(monkeypatch, provider, scoring=True)
    result = questions.score_answer(QUESTION, ANSWER)
    assert result.scored_by == "rubric"


def test_a_wild_disagreement_is_discarded_when_the_matcher_had_evidence(monkeypatch):
    """The matcher understood one point; a model claiming a perfect answer does not win."""
    answer = (
        "Tokens are the units the model predicts. I chunked documents with overlap and "
        "measured recall at 5 per cohort before touching anything else."
    )
    baseline = questions.score_answer(QUESTION, answer)
    assert baseline.quote, "this answer is meant to be one the matcher understood"
    assert 0.3 < baseline.score < 0.9, f"mid-range answer needed, got {baseline.score}"

    provider = FakeProvider(
        _verdict(100, ["tokens", "context", "limits"], [], quote=baseline.quote)
    )
    _install(monkeypatch, provider, scoring=True)
    result = questions.score_answer(QUESTION, answer)

    assert provider.calls == 1
    assert result.scored_by == "rubric", "a 100 from a model outvoted the rubric"
    assert result.score == baseline.score


def test_an_outage_falls_back_without_a_500(monkeypatch):
    provider = FakeProvider("", fail=True)
    _install(monkeypatch, provider, scoring=True)
    result = questions.score_answer(QUESTION, ANSWER)
    assert result.scored_by == "rubric"
    assert 0 < result.score <= 1


def test_prose_instead_of_json_is_not_a_verdict(monkeypatch):
    provider = FakeProvider("Sure! I'd give this answer about a 7 out of 10.")
    _install(monkeypatch, provider, scoring=True)
    assert questions.score_answer(QUESTION, ANSWER).scored_by == "rubric"


def test_a_partial_rubric_accounting_is_rejected(monkeypatch):
    """The model must judge every rubric point; half a verdict is not a verdict."""
    provider = FakeProvider(_verdict(60, ["tokens"], ["context"]))  # 'limits' unaccounted
    _install(monkeypatch, provider, scoring=True)
    assert questions.score_answer(QUESTION, ANSWER).scored_by == "rubric"


def test_a_matched_point_cannot_also_be_missing(monkeypatch):
    provider = FakeProvider(_verdict(60, ["tokens", "context"], ["context", "limits"]))
    _install(monkeypatch, provider, scoring=True)
    assert questions.score_answer(QUESTION, ANSWER).scored_by == "rubric"


def test_flattery_cannot_lift_a_fluent_non_answer(monkeypatch):
    """A model that loves a vacuous answer still runs into the vocabulary-independent floors."""
    vague_text = (
        "I have a lot of experience with this area and I am confident I could pick it up "
        "quickly on the job, because I learn fast and I communicate well with teams."
    )
    provider = FakeProvider(
        _verdict(95, ["tokens", "context", "limits"], [], quote=vague_text[:80])
    )
    _install(monkeypatch, provider, scoring=True)

    vague = questions.score_answer(QUESTION, vague_text)
    assert vague.score <= 0.45, "specificity floors must cap a model's enthusiasm"
    assert "no_specifics" in vague.flags


def test_an_answer_too_short_for_the_floors_is_never_sent(monkeypatch):
    provider = FakeProvider(_verdict(70, ["tokens", "context", "limits"], []))
    _install(monkeypatch, provider, scoring=True)
    short = questions.score_answer(QUESTION, "Tokens and context, mostly.")
    assert short.score <= 1.0
    assert provider.calls == 0, "a guaranteed-low answer should not cost a model call"
