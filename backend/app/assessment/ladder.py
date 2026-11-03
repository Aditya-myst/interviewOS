"""The assessment ladder: three short checkpoints that can turn a claim into evidence.

Why this exists next to the mock interview: an interview is expensive for the candidate
(20-30 minutes, six questions) and it is the only way a skill became `verified` before
this module. The ladder is the cheap path — three focused questions on one skill, each
one drawn from a real subtopic of `data/taxonomy.yaml`, each scored by the same
quote-gated rubric the interview uses.

Three rules, all inherited from the interview engine because they are what make a score
mean something:

1. The rubric comes from the curriculum, never from a model. Each checkpoint targets one
   subtopic and is scored on that subtopic's objective, broken into its own clauses.
2. A score needs a quote. No sentence that touches the rubric means no credit.
3. The ladder moves conceptual -> practical -> applied, and a skill is only `verified`
   when the average is high *and* no single checkpoint collapsed. One good answer about
   HTTP verbs does not verify authentication.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.interview.questions import Question, RubricItem, _content_terms
from app.parsing import taxonomy
from app.prep.lexicon import INSTRUCTION_WORDS

# Ladder level -> the taxonomy level whose subtopic it draws from.
LEVEL_SUBTOPIC = {
    "conceptual": "beginner",
    "practical": "intermediate",
    "applied": "advanced",
}
LEVELS = tuple(LEVEL_SUBTOPIC)

# Objectives are written in instruction voice ("Explain the flow", "Use verbs and status
# codes correctly"). Words that describe the *question*, not the concept, are removed
# before a rubric is built — otherwise a perfect answer stays "missing: correctly,
# without, explain" and can never clear the bar.
# Words that instruct the *candidate*, not describe the *concept*. A rubric built from
# these punishes a correct answer for not parroting the syllabus: "explain generation limits
# without mysticism" used to demand the word "mysticism" (and "work"), so a genuinely good
# answer scored 22/100. Concept terms have to be things an answer would say.
NON_CONCEPT = INSTRUCTION_WORDS | frozenset(
    {
        # adverbs and qualifiers
        "correctly", "properly", "cleanly", "quickly", "without", "really", "actually",
        "enough", "given", "following", "also", "only", "ever", "never", "always",
        # instruction verbs: what to do with knowledge, not the knowledge
        "explain", "explains", "describe", "identify", "state", "list", "know", "understand",
        "use", "uses", "using", "make", "makes", "take", "takes", "give", "gives", "get",
        "run", "runs", "write", "writes", "read", "reads", "build", "builds", "design",
        "designs", "test", "tests", "choose", "chooses", "pick", "picks", "keep", "keeps",
        "apply", "applies", "ensure", "avoid", "handle", "handles", "manage", "manages",
        "measure", "measures", "plan", "plans", "compare", "evaluate", "decide", "turn", "turns", "work", "works", "go", "goes", "put", "set", "sets", "show",
        # empty nouns
        "fundamentals", "basics", "concepts", "basic", "simple", "common", "typical",
        "correct", "right", "better", "proper", "clear", "thing", "things", "way", "ways",
        "part", "parts", "point", "points", "level", "levels", "kind", "kinds", "sort",
        "job", "jobs", "problem", "problems", "case", "cases", "example", "examples",
        "first", "next", "last", "small", "large", "good", "bad", "new", "old", "own",
        "actual", "real", "same", "different", "others", "someone", "something",
        "must", "should", "able", "need", "needs", "want", "wants", "start", "starts",
    }
)

# A clause split: objectives read like "Use verbs and status codes correctly" or
# "Measure recall@k, and explain the trade-off". Each clause is one rubric point.
_CLAUSE_SPLIT = re.compile(r"\s*(?:;|,|\band\b|\bthen\b)\s*", re.IGNORECASE)


@dataclass(frozen=True)
class Checkpoint:
    """One rung: a question, the subtopic it probes, and its rubric."""

    index: int  # 1-based, matches question_index in the contract
    level: str  # conceptual | practical | applied
    question: Question
    subtopic_id: str
    subtopic_title: str


def _root(term: str) -> str:
    """A crude root so "leaking" also matches "leak" and "internals" matches "internal".

    The interview's matcher does prefix matching on the term it is given, which means the
    rubric word "leaking" misses an answer that says "internal fields never leak". That is
    a word-matching artefact, not a gap in the answer, so the ladder stores the root
    alongside the term. The quote requirement is unchanged.
    """
    for suffix in ("ing", "ed", "es", "s"):
        # Three characters is enough for a plural: "llms" must reach "llm", or an answer that
        # says "the LLM's context window" is scored as if it never mentioned LLMs.
        floor = 3 if suffix in ("s", "es") else 4
        if term.endswith(suffix) and len(term) - len(suffix) >= floor:
            return term[: -len(suffix)]
    return term


def _concept_terms(subtopic: dict) -> tuple[str, ...]:
    """The words a good answer would actually have to contain.

    Title first: it names the concept ("tokens, context, temperature"), while the objective
    is the instruction ("explain generation limits without mysticism"). If filtering leaves
    fewer than two terms the raw title words are kept, because a rubric with no reachable
    term scores every answer zero — worse than an imperfect one.
    """
    words: list[str] = []
    for source in (str(subtopic.get("title") or ""), str(subtopic.get("objective") or "")):
        for term in _content_terms(source):
            if term in NON_CONCEPT or term in words:
                continue
            words.append(term)
    if len(words) < 2:
        fallback = [t for t in _content_terms(str(subtopic.get("title") or "")) if len(t) > 3]
        for term in fallback:
            if term not in words:
                words.append(term)
    return tuple(words)


def _objective_items(subtopic: dict) -> tuple[RubricItem, ...]:
    """Rubric for one subtopic: one item per concept term, at most six.

    One item per term, not per clause: a two-clause objective gave two rubric points, so
    missing one halved coverage and capped a good answer near 0.25. Terms keep the same
    quote requirement — a sentence has to contain the term — with finer resolution.
    """
    sub_id = str(subtopic.get("id") or "objective")
    terms = _concept_terms(subtopic)
    if not terms:
        return (RubricItem(key=sub_id, terms=(sub_id,)),)
    items = []
    for term in terms[:6]:
        root = _root(term)
        items.append(RubricItem(key=term, terms=(term,) if root == term else (term, root)))
    return tuple(items)


def _question_text(level: str, *, name: str, title: str, objective_low: str) -> str:
    """Role-agnostic wording: 'work', never 'code' or 'sprint'."""
    if level == "conceptual":
        return (
            f"{name} — {title}. Explain it in your own words: what it is for, and when "
            "would you reach for it?"
        )
    if level == "practical":
        return (
            f"{name} — {title}. Walk me through how you would {objective_low}, step by "
            "step, on a piece of real work."
        )
    return (
        f"{name} — {title}. Tell me about a time you actually had to {objective_low}: "
        "what you did, what you measured, and what broke."
    )


def _hint(level: str, objective: str) -> str:
    if level == "conceptual":
        return "A definition plus one example beats a definition alone."
    if level == "practical":
        return f"Order matters: {objective}" if objective else "Order matters."
    return "Numbers if you have them; the trade-off either way."


def build_ladder(skill: dict, *, count: int = 3) -> list[Checkpoint]:
    """Three rungs for one skill, highest-value subtopics first, no repeats.

    `skill` is a row from the same scored profile the dashboard and interview read, so a
    ladder always probes the skill the candidate was actually told to work on.
    """
    skill_id = str(skill.get("skill_id") or "")
    name = str(skill.get("name") or skill_id)
    subtopics = list(taxonomy.raw_subtopics().get(skill_id) or [])
    if not subtopics:
        return []

    by_level: dict[str, list[dict]] = {}
    for sub in subtopics:
        by_level.setdefault(str(sub.get("level") or ""), []).append(sub)

    chosen: list[tuple[str, dict]] = []
    used: set[str] = set()

    def take(level: str) -> None:
        pool = by_level.get(LEVEL_SUBTOPIC[level]) or []
        for sub in pool:
            sub_id = str(sub.get("id"))
            if sub_id not in used:
                used.add(sub_id)
                chosen.append((level, sub))
                return

    for level in LEVELS:
        if len(chosen) >= count:
            break
        take(level)

    # Not every skill has a beginner / intermediate / advanced split. Fill the rest from
    # whatever subtopics are left rather than shipping a one-question "assessment".
    for level in LEVELS:
        for sub in subtopics:
            if len(chosen) >= count:
                break
            sub_id = str(sub.get("id"))
            if sub_id not in used:
                used.add(sub_id)
                chosen.append((level, sub))

    rungs: list[Checkpoint] = []
    for i, (level, sub) in enumerate(chosen[:count], start=1):
        objective = str(sub.get("objective") or "").strip().rstrip(".")
        objective_low = objective[:1].lower() + objective[1:] if objective else f"use {name}"
        question = Question(
            text=_question_text(
                level, name=name, title=str(sub.get("title") or name), objective_low=objective_low
            ),
            question_type={
                "conceptual": "fundamentals",
                "practical": "scenario",
                "applied": "project_deep_dive",
            }[level],
            skill_id=skill_id or None,
            skill_name=name,
            source="assessment",
            rubric=_objective_items(sub),
            subtopic_id=str(sub.get("id")),
            expected_level=str(sub.get("level") or ""),
        )
        rungs.append(
            Checkpoint(
                index=i,
                level=level,
                question=question,
                subtopic_id=str(sub.get("id")),
                subtopic_title=str(sub.get("title") or ""),
            )
        )
    return rungs


def hint_for(checkpoint: Checkpoint) -> str:
    sub = (taxonomy.raw_subtopics().get(str(checkpoint.question.skill_id)) or [{}])
    objective = ""
    for candidate in sub:
        if str(candidate.get("id")) == checkpoint.subtopic_id:
            objective = str(candidate.get("objective") or "").strip().rstrip(".")
            break
    return _hint(checkpoint.level, objective)
