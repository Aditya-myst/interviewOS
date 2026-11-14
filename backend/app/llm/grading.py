"""Semantic grading: an LLM can tell that "it runs out of room" means "limits".

The rubric matcher is literal. An answer that explains token budgets and context windows
perfectly, without saying the word "limits", loses a rubric point, honest, reproducible, and
blunt. This module is the other half: when a provider is configured *and* the caller asks for
it (`LLM_SCORING=true`), a model reads the answer against the same rubric terms and returns a
verdict.

Three rules keep that from becoming a slot machine:

1. **Evidence beats eloquence.** A verdict must quote the answer verbatim; the quote is
   checked against the text, so a paraphrase is discarded. Where the matcher already found a
   quotable point, the model may only move the score within `MAX_DISAGREEMENT` of it.
2. **The deterministic hard floors stay.** No quote, too short, no specifics, those caps are
   applied by `questions.score_answer` to whatever this returns. A language model cannot buy
   credit for an answer with nothing to point at.
3. **Failure is silent and safe.** No key, an outage, a timeout, invalid JSON: return None and
   the rubric score stands, unmodified. Grading never fails a request.

Cost and latency, stated plainly: one call per uncached answer, ~0.6-3 s on the free Groq /
Gemini tiers, 0 ms on a cache hit (the gateway caches by prompt). Off by default.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from app.config import get_settings
from app.llm import get_gateway

log = logging.getLogger(__name__)

PROMPT_VERSION = 1

# How far a model may disagree with the rubric before its verdict is thrown away.
MAX_DISAGREEMENT = 0.25

# Below this, the answer cannot clear the deterministic floors anyway; calling a model to
# confirm it would add latency to a guaranteed 0.15.
MIN_ANSWER_CHARS = 80

# A quote has to be long enough to be evidence rather than a keyword.
MIN_QUOTE_CHARS = 25

# How far the model may move a score the matcher already understood. When the literal matcher
# found a quotable rubric point it has real evidence, so the model only gets a narrow band to
# argue with it. When the matcher found *nothing*, the vocabulary gap this module exists for,
# there is no evidence to defend, and the model's verified quote is the only evidence in the
# room; the caller allows it through and relies on the vocabulary-independent floors (length,
# specifics, no-quote) to keep a silver-tongued non-answer down.
MAX_DISAGREEMENT = 0.25

SYSTEM = """You grade one interview answer against one rubric.

You return JSON only, no prose, no code fences:
{"score": <integer 0-100>, "matched": [...], "missing": [...], "quote": "<sentence copied verbatim from the answer>", "rationale": "<two sentences max>"}

How to score:
- "matched" and "missing" together must be exactly the rubric points given, using their exact keys.
- Judge meaning, not vocabulary: an answer that describes the concept without using the
  rubric's word has still addressed the point. That is the entire reason you are here.
- An answer that is fluent but says nothing concrete scores below 40.
- An answer with a real example, a number or an explicit trade-off scores higher.
- Never reward confidence, length or politeness.
- "quote" must be copied character for character from the answer, the single sentence that
  earned the most credit. Paraphrasing it, or combining two sentences, invalidates your score:
  the quote is checked against the answer text and a mismatch throws the whole verdict away.

Exaggerating is the failure mode that matters: do not score above 75 unless the answer could
be quoted as evidence in a real interview loop."""


@dataclass(frozen=True)
class Verdict:
    score: float
    quote: str
    matched: tuple[str, ...]
    missing: tuple[str, ...]
    rationale: str
    provider: str
    model: str
    cached: bool
    latency_ms: int


def enabled() -> bool:
    settings = get_settings()
    return bool(getattr(settings, "llm_scoring", False)) and settings.llm_configured


def _prompt(question: str, skill: str, rubric: dict[str, str], answer: str) -> str:
    points = "\n".join(f"- {key}: {text}" for key, text in rubric.items())
    return (
        f"SKILL: {skill}\n\n"
        f"QUESTION: {question}\n\n"
        f"RUBRIC POINTS (score one point per key):\n{points}\n\n"
        f"ANSWER:\n{answer}\n\n"
        "Return the JSON object now."
    )


def _parse(raw: str, rubric_keys: list[str]) -> dict[str, Any] | None:
    """Strict: a model that answers with prose or a stray fence is a provider failure."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*|\s*```$", "", text).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    try:
        score = round(float(data["score"])) / 100
    except (KeyError, TypeError, ValueError):
        return None
    if not 0.0 <= score <= 1.0:
        return None

    matched = [str(x) for x in data.get("matched") or [] if str(x) in rubric_keys]
    missing = [str(x) for x in data.get("missing") or [] if str(x) in rubric_keys]
    # The model must account for every point; otherwise it gets its verdict thrown away
    # rather than being "repaired" into something the rubric never said.
    if sorted(set(matched) | set(missing)) != sorted(rubric_keys):
        return None
    if set(matched) & set(missing):
        return None

    quote = " ".join(str(data.get("quote") or "").split())
    if len(quote) < MIN_QUOTE_CHARS:
        return None

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "quote": quote,
        "rationale": str(data.get("rationale") or "").strip()[:400],
    }


def grade(
    *, question: str, skill: str, rubric: dict[str, str], answer: str
) -> Verdict | None:
    """A model's verdict, or None, never an exception, never a guess."""
    if not enabled():
        return None
    text = (answer or "").strip()
    if len(text) < MIN_ANSWER_CHARS or not rubric:
        return None

    keys = list(rubric)
    try:
        result = get_gateway().complete(
            _prompt(question, skill, rubric, text),
            system=SYSTEM,
            json_mode=True,
            validator=lambda raw: _parse(raw, keys),
        )
        parsed = _parse(result.text, keys)
    except Exception as exc:  # noqa: BLE001, grading must never fail a request
        # includes LLMUnavailable, provider timeouts and a validator that raises
        log.warning("llm grading unavailable (%s), the rubric stands", type(exc).__name__)
        return None

    if parsed is None:
        return None

    # The quote is the one part of a verdict that can be checked mechanically: it either
    # appears in the answer or it does not. A paraphrase is a hallucination with good manners.
    if parsed["quote"] not in " ".join((answer or "").split()):
        log.info("llm quote was not verbatim, verdict discarded")
        return None

    return Verdict(
        score=round(parsed["score"], 2),
        quote=parsed["quote"],
        matched=tuple(parsed["matched"]),
        missing=tuple(parsed["missing"]),
        rationale=parsed["rationale"],
        provider=result.provider,
        model=result.model,
        cached=result.cached,
        latency_ms=result.latency_ms,
    )


__all__ = ["MAX_DISAGREEMENT", "MIN_ANSWER_CHARS", "PROMPT_VERSION", "Verdict", "enabled", "grade"]
