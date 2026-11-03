"""Assessment sessions: state, scoring, and what a finished ladder changes.

State lives in process memory, like an interview session without a database. The score
comes from `app.interview.questions.score_answer`, which is the same quote-gated rubric
the mock interview uses — deliberately, because two scores that mean different things
would make the profile meaningless.

What a finished ladder does:

* in memory: nothing. The record exists until the process restarts, and the response
  says `persisted: false` when it happens.
* with a database: the answers are written to `assessment_answers`, the summary to
  `assessments`, and the skill is updated in `candidate_skills` — verified level,
  confidence moved halfway, and the quoted answer appended to `evidence`, so the
  dashboard can show *why* the number moved.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.assessment.ladder import Checkpoint, build_ladder, hint_for
from app.interview.questions import score_answer, specificity_level

log = logging.getLogger(__name__)

# --------------------------------------------------------------------- the score
#
# The interview's score_answer is the right instrument for a 20-minute mock: it rewards
# measured outcomes, and caps an answer that quotes nothing. A three-question checkpoint
# on "HTTP fundamentals" cannot be held to the same bar — even a perfect answer there has
# no metric to report, and the interview cap pinned it at 0.70, so a flawless ladder
# could never verify anything.
#
# So the ladder keeps the part that matters (no quote, no credit — coverage is zero)
# and scores what a checkpoint can actually show:
#
#     checkpoint = 0.85 * coverage + 0.15 * concreteness
#
# coverage     = rubric terms evidenced by a quotable sentence / rubric terms
# concreteness = 0 (no numbers or named trade-off) .. 1 (specific and measured)
#
# A skill is verified only when the average clears 0.75 AND no rung falls below 0.50 —
# one strong answer must not carry a weak one.
COVERAGE_WEIGHT = 0.85
CONCRETENESS_WEIGHT = 0.15

# A skill is only verified when the ladder is strong and consistent: one good answer
# about HTTP verbs must not verify authentication.
VERIFIED_MEAN = 0.75
VERIFIED_FLOOR = 0.50


class NotFound(LookupError):
    pass


@dataclass
class AnswerRecord:
    index: int
    level: str
    question: str
    question_type: str
    answer: str
    score: float
    quote: str | None
    matched: tuple[str, ...]
    missing: tuple[str, ...]
    why: str
    status_after: str
    specificity: int


@dataclass
class AssessmentRecord:
    id: str
    skill_id: str
    skill_name: str
    rungs: list[Checkpoint]
    answers: list[AnswerRecord] = field(default_factory=list)
    status: str = "in_progress"
    result: dict[str, Any] | None = None
    persisted: bool = False

    @property
    def index(self) -> int:
        """0-based pointer at the next unanswered rung."""
        return len(self.answers)


_STORE: dict[str, AssessmentRecord] = {}


def reset_store() -> None:
    """Tests only."""
    _STORE.clear()


def _skill_name(skill: dict) -> str:
    return str(skill.get("name") or skill.get("skill_id") or "")


def start(skill: dict, *, question_total: int = 3) -> AssessmentRecord:
    rungs = build_ladder(skill, count=question_total)
    if not rungs:
        raise ValueError(
            f"no subtopics for {skill.get('skill_id')!r} — this skill has nothing to assess"
        )
    record = AssessmentRecord(
        id=str(uuid.uuid4()),
        skill_id=str(skill.get("skill_id") or ""),
        skill_name=_skill_name(skill),
        rungs=rungs,
    )
    _STORE[record.id] = record
    return record


def get(assessment_id: str) -> AssessmentRecord:
    record = _STORE.get(assessment_id)
    if record is None:
        raise NotFound(assessment_id)
    return record


def _question_payload(checkpoint: Checkpoint) -> dict[str, Any]:
    question = checkpoint.question
    return {
        "text": question.text,
        "skill_name": question.skill_name,
        "rubric_size": len(question.rubric),
        "question_type": question.question_type,
        "hint": hint_for(checkpoint),
        "level": checkpoint.level,
        "subtopic": checkpoint.subtopic_title,
    }


def state(record: AssessmentRecord) -> dict[str, Any]:
    """The contract's AssessmentState, with nothing invented."""
    payload: dict[str, Any] = {
        "assessment_id": record.id,
        "skill_id": record.skill_id,
        "skill_name": record.skill_name,
        "level": record.rungs[min(record.index, len(record.rungs) - 1)].level,
        "status": record.status,
        "question_index": min(record.index + 1, len(record.rungs)),
        "question_total": len(record.rungs),
        "question": None,
        "feedback": None,
        "result": record.result,
        "persisted": record.persisted,
        "answers": [
            {
                "index": a.index,
                "level": a.level,
                "question": a.question,
                "score": a.score,
                "status_after": a.status_after,
                "quote": a.quote,
                "why": a.why,
                "matched": [m.replace("-", " ") for m in a.matched],
                "missing": [m.replace("-", " ") for m in a.missing],
            }
            for a in record.answers
        ],
    }
    if record.status == "in_progress" and record.index < len(record.rungs):
        payload["question"] = _question_payload(record.rungs[record.index])
        if record.answers:
            last = record.answers[-1]
            rubric_size = len(record.rungs[last.index - 1].question.rubric) or 1
            payload["feedback"] = {
                # Three dimensions, all measured. No "communication": this is typed text,
                # and a number for how someone sounds would be invented.
                "scores": {
                    "technical_correctness": last.score,
                    "depth": round(len(last.matched) / rubric_size, 2),
                    "practical_ability": round(min(1.0, last.specificity / 2), 2),
                },
                "missing_concepts": [m.replace("-", " ") for m in last.missing],
                "summary": last.why,
                "quote": last.quote,
                "matched": [m.replace("-", " ") for m in last.matched],
                "scored_by": "rubric",
            }
    return payload


def _rung_why(checkpoint, result, coverage: float, specificity: int, score: float) -> str:
    if not result.quote:
        return (
            "Nothing here could be quoted, so it cannot count as evidence for this "
            "checkpoint. Name the work, the step, and what changed."
        )
    parts = [
        (f"{round(coverage * 100)}% of this checkpoint's rubric was evidenced "
        f"({len(result.matched)} of {len(checkpoint.question.rubric)} points)")
    ]
    if result.missing:
        parts.append("still missing: " + ", ".join(m.replace("-", " ") for m in result.missing))
    parts.append("specific enough to be useful" if specificity >= 1 else "general — add what you did and what changed")
    return "; ".join(parts) + f". Score {round(score * 100)}."


def _inferred_level(mean: float) -> str:
    """Deliberately conservative: a three-question ladder rarely justifies "expert".

    The verified bar is 0.75, so 0.75-0.90 reads as advanced and only a near-perfect
    ladder claims expert. Calling an 85 an expert level would be the profile flattering
    the candidate, which is the one thing this product cannot do.
    """
    if mean >= 0.90:
        return "expert"
    if mean >= 0.72:
        return "advanced"
    if mean >= 0.50:
        return "intermediate"
    if mean > 0:
        return "beginner"
    return "none"


def _status_after(mean: float, floor: float) -> str:
    if mean >= VERIFIED_MEAN and floor >= VERIFIED_FLOOR:
        return "verified"
    if mean >= 0.50:
        return "developing"
    if mean >= 0.30:
        return "weak"
    return "needs_revision"


def _summarise(record: AssessmentRecord) -> dict[str, Any]:
    scores = [a.score for a in record.answers]
    mean = round(sum(scores) / len(scores), 2) if scores else 0.0
    floor = min(scores) if scores else 0.0
    status_after = _status_after(mean, floor)
    weak = [a for a in record.answers if a.score < 0.5]
    return {
        "inferred_level": _inferred_level(mean),
        "status_after": status_after,
        # Three checkpoints are real evidence but not a full interview; the ceiling says so.
        "confidence": round(min(0.90, 0.35 + 0.55 * mean), 2),
        "mean_score": mean,
        "lowest_score": round(floor, 2),
        "checkpoints": len(record.answers),
        "verified": status_after == "verified",
        "why": (
            f"Average {round(mean * 100)} across {len(record.answers)} checkpoints, "
            f"lowest {round(floor * 100)}. "
            + (
                "Every rung held up, so this skill is verified."
                if status_after == "verified"
                else "A skill is verified only when the average clears 75 and no rung falls below 50."
            )
        ),
        "redo": [
            {"question": a.question, "score": a.score, "quote": a.quote, "why": a.why}
            for a in weak
        ],
    }


def answer(record: AssessmentRecord, text: str) -> dict[str, Any]:
    """Grade one rung, then hand back the contract's AssessmentState."""
    if record.status == "completed":
        raise ValueError("this assessment is already completed")
    checkpoint = record.rungs[record.index]
    result = score_answer(checkpoint.question, text or "")
    specificity = specificity_level(text or "")
    total = len(checkpoint.question.rubric) or 1
    # The quote gate survives verbatim: no quotable sentence means no coverage, whatever
    # else the answer contained.
    coverage = len(result.matched) / total if result.quote else 0.0
    concreteness = min(1.0, specificity / 2)
    score = round(COVERAGE_WEIGHT * coverage + CONCRETENESS_WEIGHT * concreteness, 2)
    band = _status_after(score, score)
    record.answers.append(
        AnswerRecord(
            index=checkpoint.index,
            level=checkpoint.level,
            question=checkpoint.question.text,
            question_type=checkpoint.question.question_type,
            answer=text or "",
            score=score,
            quote=result.quote,
            matched=result.matched,
            missing=result.missing,
            why=_rung_why(checkpoint, result, coverage, specificity, score),
            status_after=band,
            specificity=specificity,
        )
    )
    if record.index >= len(record.rungs):
        record.status = "completed"
        record.result = _summarise(record)
    return state(record)


# ------------------------------------------------------------------ persistence


def writeback(db_session, *, user_id: str, record: AssessmentRecord) -> bool:
    """Record the ladder and move the skill. Returns False when it could not be saved.

    Every failure is logged and swallowed: a demo that shows a scored ladder and says it
    was not saved is better than a 500 after the candidate did the work.
    """
    from decimal import Decimal

    from sqlalchemy import select

    from app.models import Assessment, AssessmentAnswer, CandidateSkill

    try:
        row = Assessment(
            id=uuid.UUID(record.id),
            user_id=uuid.UUID(str(user_id)),
            skill_id=record.skill_id,
            level=record.rungs[0].level,
            status=record.status,
            question_index=min(record.index, len(record.rungs)),
            question_total=len(record.rungs),
            plan=[
                {
                    "index": r.index,
                    "level": r.level,
                    "subtopic": r.subtopic_id,
                    "rubric": [item.key for item in r.question.rubric],
                }
                for r in record.rungs
            ],
            inferred_level=(record.result or {}).get("inferred_level"),
            status_after=(record.result or {}).get("status_after"),
            confidence=Decimal(str((record.result or {}).get("confidence") or 0)),
            completed_at=datetime.now(UTC),
        )
        db_session.add(row)
        for a in record.answers:
            db_session.add(
                AssessmentAnswer(
                    user_id=uuid.UUID(str(user_id)),
                    assessment_id=uuid.UUID(record.id),
                    question_index=a.index,
                    question_text=a.question,
                    question_type=_question_type(a.question_type),
                    answer_text=a.answer,
                    scores={"score": a.score, "status_after": a.status_after},
                    missing_concepts=list(a.missing),
                    feedback=a.why,
                )
            )

        skill = db_session.execute(
            select(CandidateSkill).where(
                CandidateSkill.user_id == uuid.UUID(str(user_id)),
                CandidateSkill.skill_id == record.skill_id,
            )
        ).scalar_one_or_none()

        if skill is not None and record.result:
            new_conf = float(record.result["confidence"])
            current = float(skill.confidence or 0)
            # Halfway, same as the interview: one measurement does not overwrite a profile.
            skill.confidence = Decimal(str(round(current + (new_conf - current) / 2, 2)))
            skill.verified_level = record.result["inferred_level"]
            if record.result["status_after"] == "verified":
                skill.status = "verified"
            elif skill.status in ("unverified", "claimed"):
                skill.status = "developing"
            evidence = list(skill.evidence or [])
            for a in record.answers:
                if a.quote:
                    evidence.append(
                        {
                            "type": "assessment_answer",
                            "quote": a.quote,
                            "score": a.score,
                            "subtopic": record.rungs[a.index - 1].subtopic_id,
                            "at": datetime.now(UTC).isoformat(),
                        }
                    )
            skill.evidence = evidence
            skill.last_assessed_at = datetime.now(UTC)
        db_session.commit()
        record.persisted = True
        return True
    except Exception:  # persistence is best effort, and the response says so
        log.exception("assessment writeback failed — the ladder stays in memory")
        db_session.rollback()
        return False


def _question_type(value: str) -> str:
    allowed = {
        "fundamentals",
        "advanced",
        "coding",
        "debugging",
        "project_deep_dive",
        "scenario",
        "system_design",
        "behavioral",
    }
    return value if value in allowed else "fundamentals"
