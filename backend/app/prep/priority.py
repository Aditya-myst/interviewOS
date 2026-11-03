"""Merge resume claims with JD requirements and score them. Pure functions only.

Why not ask a model which skill matters most: because "why is this first?" is the
question a user will ask, and the answer has to be the same tomorrow. The formula is
the one in contracts/ENUMS.md §3 —

    priority = jd_importance × gap × interview_relevance

— with band thresholds >=0.55 critical, >=0.35 high, >=0.18 medium, else low. The
fixture profile was produced with this formula, which is why its numbers and the
pipeline's numbers land in the same place.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.parsing.jd import ParsedJD, Requirement
from app.parsing.resume import ParsedResume

# contracts/ENUMS.md §2 — `listed` shares beginner's numeric value on purpose
LEVEL_VALUE = {
    "none": 0.0,
    "listed": 0.25,
    "beginner": 0.4,
    "intermediate": 0.55,
    "advanced": 0.75,
    "expert": 0.95,
}
LEVEL_ORDER = ["none", "listed", "beginner", "intermediate", "advanced", "expert"]

BANDS = ((0.55, "critical"), (0.35, "high"), (0.18, "medium"), (0.0, "low"))


def _dedupe_evidence(items: list[dict]) -> list[dict]:
    """One entry per (type, quote, span), ignoring how the line happened to wrap.

    A PDF that breaks a sentence across lines produces the same sentence twice with
    different newlines; the profile then showed the candidate the same proof twice, which
    reads like padding.
    """
    seen: set[tuple] = set()
    out: list[dict] = []
    for item in items:
        quote = " ".join(str(item.get("quote") or "").split())
        key = (item.get("type"), quote, item.get("start"), item.get("end"))
        loose = (item.get("type"), quote)
        if key in seen or (not quote and loose in seen):
            continue
        if any(existing[1] == loose[1] and existing[0] == loose[0] for existing in seen):
            continue
        seen.add(key)
        seen.add(loose)
        out.append(item)
    return out


def band(priority: float) -> str:
    for threshold, name in BANDS:
        if priority >= threshold:
            return name
    return "low"


def gap(expected: str, held: str) -> float:
    """How far the JD's expectation is above what we can currently show."""
    return round(max(0.0, LEVEL_VALUE.get(expected, 0.0) - LEVEL_VALUE.get(held, 0.0)), 2)


@dataclass
class ScoredSkill:
    skill_id: str
    name: str
    category: str
    status: str
    claimed_level: str | None
    verified_level: str | None
    expected_level: str
    confidence: float
    jd_importance: float
    interview_relevance: float
    gap: float
    priority: float
    priority_band: str
    explanation: str
    in_resume: bool
    in_jd: bool
    evidence: list[dict]

    def as_json(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "claimed_level": self.claimed_level,
            "verified_level": self.verified_level,
            "expected_level": self.expected_level,
            "confidence": self.confidence,
            "jd_importance": self.jd_importance,
            "interview_relevance": self.interview_relevance,
            "gap": self.gap,
            "priority": self.priority,
            "priority_band": self.priority_band,
            "explanation": self.explanation,
            "in_resume": self.in_resume,
            "in_jd": self.in_jd,
            "last_assessed_at": None,
            "evidence": self.evidence,
        }


def _explain(
    *, name: str, in_resume: bool, in_jd: bool, requirement: Requirement | None,
    claimed: str | None, expected: str, gap_value: float, band_name: str,
) -> str:
    """One sentence, deterministic, and specific about which side is thin."""
    if in_jd and not in_resume:
        return (
            f"{name} is {requirement.requirement_type if requirement else 'required'} in the JD "
            f"at {expected} level and appears nowhere in your resume — the largest kind of gap."
        )
    if in_resume and in_jd:
        trailing = (
            "your resume shows it only in passing" if claimed == "listed"
            else f"your resume claims {claimed}"
        )
        requirement_word = requirement.requirement_type if requirement else "required"
        return (
            f"{requirement_word.capitalize()} at {expected} level in the JD; {trailing}, "
            f"so the gap is {gap_value:.2f} and prep ranks it {band_name}."
        )
    if in_resume:
        return (
            f"{name} is on your resume but not in this JD — kept for coverage at "
            f"{claimed} level, ranked {band_name} against the interview's own weighting."
        )
    return f"No evidence either side; ranked {band_name}."


def score(resume: ParsedResume, jd: ParsedJD, *, verified: dict[str, dict] | None = None) -> list[ScoredSkill]:
    """`verified` is what the assessment engine will pass in later: skill_id -> {level, evidence}.
    The resume never sets a verified level, which is why it defaults to empty here."""
    from app.parsing import taxonomy

    vocab = taxonomy.load()
    verified = verified or {}
    claims = {c.skill_id: c for c in resume.skills}
    requirements = {r.skill_id: r for r in jd.requirements}

    rows: list[ScoredSkill] = []
    for skill_id in sorted(set(claims) | set(requirements)):
        skill = vocab.get(skill_id)
        if skill is None:
            continue
        claim = claims.get(skill_id)
        requirement = requirements.get(skill_id)

        claimed_level = claim.claimed_level if claim else None
        verification = verified.get(skill_id) or {}
        verified_level = verification.get("level")

        expected_level = requirement.expected_level if requirement else "intermediate"
        held = verified_level or claimed_level or "none"
        gap_value = gap(expected_level, held)

        if requirement is not None:
            jd_importance = requirement.jd_importance
        else:
            # not in the JD: ENUMS §3 says interview_relevance is the default weight
            jd_importance = round(skill.interview_relevance * 0.5, 2)

        priority = round(jd_importance * gap_value * skill.interview_relevance, 3)
        band_name = band(priority)

        if verified_level:
            status = "verified"
        elif claim is not None:
            status = "claimed"
        else:
            status = "unverified"

        evidence = list(claim.evidence) if claim else []
        if requirement is not None:
            # A JD quote is not resume evidence. This used to be retyped as
            # resume_skill_list, which put "followers alone are not the metric" on the
            # candidate's own evidence list — the exact opposite of what this product
            # promises. It keeps its own type and gains the document it came from.
            evidence += [
                dict(item, type="jd_requirement", document="jd")
                for item in requirement.evidence
            ]
        if verification.get("evidence"):
            evidence += verification["evidence"]
        for item in evidence:
            item.setdefault("document", "resume")
        evidence = _dedupe_evidence(evidence)

        rows.append(
            ScoredSkill(
                skill_id=skill_id,
                name=skill.name,
                category=skill.category,
                status=status,
                claimed_level=claimed_level,
                verified_level=verified_level,
                expected_level=expected_level,
                confidence=claim.confidence if claim else 0.0,
                jd_importance=jd_importance,
                interview_relevance=skill.interview_relevance,
                gap=gap_value,
                priority=priority,
                priority_band=band_name,
                explanation=_explain(
                    name=skill.name, in_resume=claim is not None, in_jd=requirement is not None,
                    requirement=requirement, claimed=claimed_level, expected=expected_level,
                    gap_value=gap_value, band_name=band_name,
                ),
                in_resume=claim is not None,
                in_jd=requirement is not None,
                evidence=evidence[:4],
            )
        )

    rows.sort(key=lambda row: (-row.priority, row.skill_id))
    return rows


def next_level(level: str | None) -> str:
    """The rung above a claimed level — used by the plan, not by the score."""
    if not level or level not in LEVEL_ORDER:
        return "beginner"
    index = LEVEL_ORDER.index(level)
    return LEVEL_ORDER[min(index + 1, len(LEVEL_ORDER) - 1)]
