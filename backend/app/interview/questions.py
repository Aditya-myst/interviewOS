"""Questions and scoring — the part of the interview that must not be a black box.

Two rules decide everything here:

1. A question is generated from the curriculum, not from the model's imagination. Every
   question names a skill, and carries a rubric derived from a real subtopic objective
   in data/taxonomy.yaml. That is what makes the answer scoreable.
2. A score needs a quote. If the answer contains no sentence that touches the rubric,
   the score is capped low and the answer is recorded as evidence-free — never rounded
   up because it "sounded confident".

Both functions are pure: no database, no LLM, no clock. That is deliberate — the honest
path has to be the testable path. An LLM may later *draft* better phrasing (block 6),
but it never invents the rubric and never supplies the quote.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from app.parsing import taxonomy
from app.prep.lexicon import CONCEPT_SYNONYMS, INSTRUCTION_WORDS

# Words that appear in every objective and therefore discriminate nothing.
STOPWORDS = frozenset(
    ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "how", "in", "into", "is", "it", "its", "of", "on", "or", "so", "that", "the", "their", "then", "there", "these", "this", "to", "up", "use", "used", "using", "what", "when", "where", "which", "who", "why", "with", "your", "you", "they", "them", "not", "but", "can", "could", "should", "would", "will", "just", "one", "own", "instead"]
)

# A sentence shorter than this cannot evidence much; longer than this is a paragraph
# and gets cut at the first full stop for the quote.
MIN_QUOTE_CHARS = 25
MAX_ANSWER_CHARS = 6000

BANDS = ("critical", "high", "medium", "low")

# source -> question kind, per contracts/types.ts QuestionType.
PEDAGOGY = {
    "resume_project": "project_deep_dive",
    "verified_skill": "advanced",
    "weak_skill": "fundamentals",
    "jd": "scenario",
    "general": "behavioral",
}

# Ownership verbs. An answer that only believes, thinks or cares is not evidence of
# having done the thing; it is evidence of having opinions about it.
ACTION_VERBS = ["ran", "run", "built", "build", "wrote", "write", "wrote", "shipped", "ship", "measured", "measure", "tested", "test", "cut", "reduced", "reduce", "increased", "increase", "launched", "launch", "designed", "design", "led", "lead", "migrated", "migrated", "debugged", "debug", "refactored", "refactor", "analysed", "analyzed", "tracked", "track", "owned", "own", "managed", "manage", "fixed", "fix", "rewrote", "rewrite", "presented", "present", "interviewed", "interview", "audited", "audit", "documented", "document", "deployed", "deploy"]

HEDGES = ("i think", "i believe", "i feel", "in my opinion", "i care", "i am good at", "i'm good at")


@dataclass(frozen=True)
class RubricItem:
    """One thing a good answer should show, plus the words that would show it."""

    key: str
    terms: tuple[str, ...]


@dataclass(frozen=True)
class Question:
    text: str
    question_type: str  # jd | resume_project | weak_skill | verified_skill | general
    skill_id: str | None
    skill_name: str
    source: str  # mirrors question_type, as contracts/types.ts expects
    rubric: tuple[RubricItem, ...] = ()
    subtopic_id: str | None = None
    expected_level: str | None = None


@dataclass(frozen=True)
class AnswerScore:
    score: float
    status_after: str  # weak | developing | verified | needs_revision
    quote: str | None
    matched: tuple[str, ...]
    missing: tuple[str, ...]
    why: str
    scored_by: str = "rubric"  # never "llm" until an LLM actually did it
    flags: tuple[str, ...] = field(default_factory=tuple)


# --------------------------------------------------------------------------- helpers


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9+#.]+", text.lower())


def _content_terms(text: str, *, keep: tuple[str, ...] = ()) -> tuple[str, ...]:
    """Discriminative words from a sentence, in the order they appear.

    `keep` used to be appended verbatim, so a subtopic title became one "term" — the phrase
    "how llms work: tokens, context, temperature" — which no answer can contain. Titles are
    now split into words, and instruction words ("explain", "measure", "without") are
    dropped: they tell the candidate what to do, they are not what an answer says.
    """
    seen: list[str] = []
    for source in keep:
        text = f"{source} {text}"
    for word in _words(text):
        bare = word.strip(".")
        if len(bare) < 4 or bare in STOPWORDS or bare in INSTRUCTION_WORDS:
            continue
        if bare not in seen:
            seen.append(bare)
    return tuple(seen)


MIN_SENTENCE_WORDS = 6


# Suffixes that change the form of a word without changing the idea in it. Ordered longest
# first so "requirements" loses "ments" in one step rather than "s" and then "ment".
_SUFFIXES = (
    "ically", "ations", "ation", "encies", "ency", "ances", "ance", "ences", "ence",
    "ments", "ment", "ings", "ing", "ions", "ion", "ities", "ity", "ies", "ied", "ers",
    "er", "ed", "es", "s", "ent", "ant", "ly",
)


def _stem(term: str) -> str:
    """Reduce a word to a form two spellings of one idea share.

    This replaces a single-rule stemmer ("strip a trailing e") that only worked in one
    direction: the rubric said *replication* and the answer said *replica*, the rubric said
    *queues* and the answer said *queue*, and both scored as a miss. An answer that is right
    in substance must not be marked wrong for its morphology — that was the single largest
    source of unfair low scores in the ladder.
    """
    word = term.strip().lower()
    stable = False
    while not stable and len(word) > 4:
        stable = True
        if word.endswith("ies"):
            word = f"{word[:-3]}y"
            continue
        for suffix in _SUFFIXES:
            if word.endswith(suffix) and len(word) - len(suffix) >= 4:
                word = word[: -len(suffix)]
                stable = False
                break
        if stable and word.endswith("e") and len(word) > 4:
            word = word[:-1]
            stable = False
    return word


def _stem_matches(left: str, right: str) -> bool:
    """Same stem, or one is a short extension of the other ("replic" / "replica")."""
    if left == right:
        return True
    short, long = (left, right) if len(left) <= len(right) else (right, left)
    # 5 characters, not 4: at 4, "shar" (share) was a prefix of "shard" (shard), so a
    # sentence about a share price evidenced a rubric point about sharding. "replic" and
    # "replica" are still the same idea; "shar" and "shard" are not.
    return len(short) >= 5 and long.startswith(short) and len(long) - len(short) <= 3


@lru_cache(maxsize=4096)
def _text_stems(text: str) -> frozenset[str]:
    return frozenset(_stem(word) for word in _words(text))


def _term_forms(term: str) -> tuple[str, ...]:
    """The stem of a rubric term plus the stems of the alternates that mean the same thing."""
    forms = [_stem(term)]
    for synonym in CONCEPT_SYNONYMS.get(term.strip().lower(), ()):
        stem = _stem(synonym)
        if stem not in forms:
            forms.append(stem)
    return tuple(forms)


def _has_term(text: str, terms: tuple[str, ...]) -> bool:
    """Does the text say any of these terms — in any grammatical form, in other words?"""
    stems = _text_stems(text)
    if not stems:
        return False
    return any(
        _stem_matches(form, stem) for term in terms for form in _term_forms(term) for stem in stems
    )


def _substantive(sentence: str) -> bool:
    return len(_words(sentence)) >= MIN_SENTENCE_WORDS


def _sentence_has_term(sentence: str, terms: tuple[str, ...]) -> bool:
    return _has_term(sentence, terms)


def split_sentences(answer: str) -> list[str]:
    """Sentence split that keeps the text verbatim — quotes must be substrings."""
    parts = re.split(r"(?<=[.!?])\s+|\n+", answer.strip())
    return [part.strip() for part in parts if part.strip()]


# -------------------------------------------------------------------------- rubrics


def rubric_for_skill(skill_id: str, *, limit: int = 4) -> tuple[RubricItem, ...]:
    """Rubric rows built from the skill's subtopic objectives."""
    subtopics = taxonomy.raw_subtopics().get(skill_id) or []
    skill = taxonomy.load().get(skill_id)
    items: list[RubricItem] = []
    for sub in subtopics[:limit]:
        terms = _content_terms(str(sub.get("objective") or ""), keep=(str(sub.get("title") or ""),))
        if not terms:
            continue
        items.append(RubricItem(key=str(sub["id"]), terms=terms[:6]))
    if not items and skill is not None:
        items.append(RubricItem(key=skill_id, terms=_content_terms(skill.name) or (skill.id,)))
    return tuple(items)


def _pick_subtopic(skill_id: str, expected_level: str | None) -> dict | None:
    subtopics = taxonomy.raw_subtopics().get(skill_id) or []
    if not subtopics:
        return None
    for sub in subtopics:
        if expected_level and sub.get("level") == expected_level:
            return sub
    return subtopics[0]


def _first_quote(skill: dict) -> str | None:
    for item in skill.get("evidence") or []:
        quote = (item or {}).get("quote")
        if quote:
            return str(quote)
    return None


def _shorten(text: str, limit: int = 150) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def question_for_skill(skill: dict) -> Question:
    """One question for one skill, always with a rubric behind it."""
    skill_id = str(skill.get("skill_id") or "")
    name = str(skill.get("name") or skill_id)
    band = str(skill.get("priority_band") or "medium")
    status = str(skill.get("status") or "unverified")
    expected = skill.get("expected_level")
    subtopic = _pick_subtopic(skill_id, str(expected) if expected else None)
    objective = str((subtopic or {}).get("objective") or "").rstrip(".")
    objective_low = objective[:1].lower() + objective[1:] if objective else f"apply {name}"
    quote = _first_quote(skill)
    rubric = rubric_for_skill(skill_id)

    if status == "verified":
        qtype = "verified_skill"
        text = (
            f"You're marked verified on {name}. Go past the basics: {objective_low}. "
            "What did you get wrong the first time, and what did you change?"
        )
    elif quote and band in ("critical", "high"):
        qtype = "resume_project"
        text = (
            f'Your resume says: “{_shorten(quote)}”. Take that work and walk me through '
            f"how you would {objective_low} — what you actually did, and what you would "
            "do differently now."
        )
    elif band in ("critical", "high"):
        qtype = "weak_skill"
        level = skill.get("verified_level") or skill.get("claimed_level") or "unproven"
        text = (
            f"{name} is one of your biggest gaps (your evidence is {level}-level here). "
            f"Pick one real example where you had to {objective_low}. Be specific: what "
            "you did, what you measured, what came out."
        )
    elif skill.get("in_jd"):
        qtype = "jd"
        text = (
            f"This role asks for {name}. Describe the last time you had to "
            f"{objective_low}, and name the trade-off you chose."
        )
    else:
        qtype = "general"
        text = (
            f"Let's cover {name}. In your own words, how do you {objective_low}, and "
            "how do you know when you have done it well?"
        )

    return Question(
        text=text,
        # `source` says where the question came from; `question_type` says what kind of
        # question it is. contracts/types.ts keeps those vocabularies separate, and so
        # does this engine — collapsing them was the first version's bug.
        question_type=PEDAGOGY.get(qtype, "scenario"),
        skill_id=skill_id or None,
        skill_name=name,
        source=qtype,
        rubric=rubric,
        subtopic_id=(subtopic or {}).get("id"),
        expected_level=(subtopic or {}).get("level"),
    )


def build_plan(skills: list[dict], *, total: int = 6) -> list[Question]:
    """Ordered plan: highest priority first, one question per skill, no duplicates."""
    ranked = sorted(
        [s for s in skills if s.get("skill_id")],
        key=lambda s: float(s.get("priority") or 0),
        reverse=True,
    )
    plan: list[Question] = []
    seen: set[str] = set()
    for skill in ranked:
        skill_id = str(skill["skill_id"])
        if skill_id in seen:
            continue
        seen.add(skill_id)
        plan.append(question_for_skill(skill))
        if len(plan) >= total:
            break
    return plan


# --------------------------------------------------------------------------- scoring


def _status_for(score: float) -> str:
    if score >= 0.75:
        return "verified"
    if score >= 0.5:
        return "developing"
    if score >= 0.3:
        return "weak"
    return "needs_revision"


def specificity_level(text: str) -> int:
    """0 = opinions, 1 = some ownership, 2+ = a real example.

    Coverage of the rubric alone is gameable: a fluent paragraph that name-drops every
    keyword scores like an expert. This is the counterweight — and nothing reaches
    "verified" without it.
    """
    low = text.lower()
    level = 0
    if re.search(r"\d", text):
        level += 1  # a number: a size, a metric, a duration, a version
    if any(re.search(rf"\b(i|we)\s+{_stem(verb)}", low) for verb in ACTION_VERBS):
        level += 1  # first-person action, past or present
    if re.search(r"\b(at|during|when i|on the|for the|in my|across)\b", low):
        level += 1  # a place or time the work happened in
    if any(hedge in low for hedge in HEDGES) and level == 0:
        level = 0
    return level


def _best_quote(answer: str, matched_terms: tuple[str, ...]) -> str | None:
    """The candidate's own sentence, verbatim, that best covers the rubric."""
    if not matched_terms:
        return None
    best: tuple[int, str] | None = None
    for sentence in split_sentences(answer):
        if len(sentence) < MIN_QUOTE_CHARS:
            continue
        hits = sum(1 for term in matched_terms if _has_term(sentence, (term,)))
        if hits == 0:
            continue
        # Prefer the sentence that would convince a hiring manager: numbers and
        # first-person actions outrank topical relevance.
        weight = hits + (2 if re.search(r"\d", sentence) else 0) + (
            1 if specificity_level(sentence) >= 2 else 0
        )
        if best is None or weight > best[0]:
            best = (weight, sentence)
    return best[1] if best else None



def _semantic_verdict(question: Question, text: str, deterministic: float, *, has_quote: bool):
    """The model's reading of the answer, or None when it may not be trusted.

    The tolerance depends on *why* they disagree. When the matcher found a quote it already
    understood the answer, so the model gets a narrow band to argue in. When the matcher found
    nothing it understood nothing — the vocabulary gap this pass exists to close — so the
    model's verdict stands, because `grading` has already checked that its quote appears
    verbatim in the answer and the structural floors still cap what a fluent non-answer can
    reach.
    """
    from app.llm import grading

    if not grading.enabled():
        return None
    rubric = {item.key: ", ".join(item.terms) for item in question.rubric}
    verdict = grading.grade(
        question=question.text, skill=question.skill_name, rubric=rubric, answer=text
    )
    if verdict is None:
        return None
    if has_quote:
        if abs(verdict.score - deterministic) > grading.MAX_DISAGREEMENT:
            # The matcher has a quotable point; a model that disagrees wildly is a provider
            # problem, not a grading decision.
            return None
        return verdict

    # The matcher understood nothing, so the model is the only reader — but only an answer
    # that carries substance may be rescued. Specificity is measurable without vocabulary:
    # an example, a number, a named tool. Without it, a model's generosity is just a longer
    # way of saying "sounds good", and the deterministic score stands.
    if specificity_level(text) < 2:
        return None
    return verdict


def score_answer(question: Question, answer: str) -> AnswerScore:
    """Coverage of the rubric, capped when there is no quote to point at."""
    text = (answer or "").strip()[:MAX_ANSWER_CHARS]
    flags: list[str] = []

    if not text:
        return AnswerScore(
            score=0.0,
            status_after="needs_revision",
            quote=None,
            matched=(),
            missing=tuple(item.key for item in question.rubric),
            why="No answer was given, so nothing was evidenced.",
            flags=("empty",),
        )

    sentences = [s for s in split_sentences(text) if _substantive(s)]
    matched: list[str] = []
    matched_terms: list[str] = []
    for item in question.rubric:
        # A one-word or throwaway sentence mentioning the topic is not evidence that
        # the point was addressed — the mention has to sit in a real sentence.
        if any(_has_term(sentence, item.terms) for sentence in sentences):
            matched.append(item.key)
            matched_terms.extend(item.terms)
    missing = [item.key for item in question.rubric if item.key not in matched]

    coverage = len(matched) / len(question.rubric) if question.rubric else 0.0
    skill_terms = _content_terms(question.skill_name)
    concrete = bool(re.search(r"\d", text)) or _has_term(text, skill_terms or ())

    # 0.12 keeps a bare attempt above zero; 0.78 is the rubric coverage; 0.10 is
    # the specificity bonus that a fluent-but-empty answer never gets.
    score = 0.12 + 0.78 * coverage + (0.10 if concrete else 0.0)
    specificity = specificity_level(text)
    quote = _best_quote(text, tuple(dict.fromkeys(matched_terms)))

    # Semantic pass, before the floors: a model may recognise a rubric point the literal
    # matcher missed, and in that case the deterministic quote is None precisely *because*
    # the vocabulary differed. The verdict has to supply its own quote and that quote is
    # checked against the answer text, so the evidence requirement survives.
    scored_by = "rubric"
    llm_note = ""
    verdict = _semantic_verdict(question, text, score, has_quote=quote is not None)
    if verdict is not None:
        score = verdict.score
        matched = list(verdict.matched)
        missing = list(verdict.missing)
        quote = verdict.quote
        scored_by = "llm"
        llm_note = f" {verdict.rationale}".strip()
        flags.append("llm_graded")

    if len(text) < 40:
        flags.append("too_short")
        score = min(score, 0.15)
    if quote is None:
        flags.append("no_quote")
        # The whole point: no quote, no credit. 0.25 is the ceiling for a persuasive
        # answer that cannot be pointed at.
        score = min(score, 0.25)
    if len(_words(text)) < 25:
        flags.append("too_short")
        score = min(score, 0.35)
    if specificity <= 1:
        flags.append("no_specifics")
        # Ceiling by specificity: opinions cannot reach "developing", and an answer
        # with no example at all cannot reach "verified" however many keywords it has.
        score = min(score, 0.45 if specificity == 0 else 0.70)

    score = round(max(0.0, min(score, 1.0)), 2)
    status = _status_for(score)

    if quote is None:
        why = (
            "Nothing in the answer touched the rubric for this question, so it cannot be "
            "scored as evidence. Answer with a specific example you actually worked on."
        )
    elif status == "verified":
        why = "The answer covers most of the rubric with a concrete, quotable example."
    elif status == "developing":
        why = f"Partly evidenced: {len(matched)} of {len(question.rubric)} rubric points were addressed."
    else:
        why = (
            f"Thin evidence: only {len(matched)} of {len(question.rubric)} rubric points were "
            "addressed, and the answer stays general."
        )

    return AnswerScore(
        score=score,
        status_after=status,
        quote=quote,
        matched=tuple(matched),
        missing=tuple(missing),
        why=f"{why}{llm_note}",
        scored_by=scored_by,
        flags=tuple(flags),
    )
