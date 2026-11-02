"""JD parsing, priority scoring and the profile payload.

The formula is contracts/ENUMS.md §3: priority = jd_importance × gap ×
interview_relevance, bands at .55/.35/.18. These tests pin the arithmetic so a
"why is this first?" answer stays true tomorrow.
"""
import json
import pathlib

from app.parsing import jd as jd_mod
from app.parsing import resume as resume_mod
from app.parsing.extract import extract
from app.prep import priority
from app.prep.profile import build_profile

DATA = pathlib.Path(__file__).parent / "data"
RESUME_TEXT = (DATA / "sample_resume.txt").read_text()
JD_TEXT = (DATA / "sample_jd.txt").read_text()


def parsed_resume():
    return resume_mod.parse(extract("resume.txt", RESUME_TEXT.encode()))


def parsed_jd():
    return jd_mod.parse(JD_TEXT)


# ── JD parsing ────────────────────────────────────────────────────────────────
def test_required_and_preferred_are_not_mixed_up():
    parsed = parsed_jd()
    by_id = {r.skill_id: r for r in parsed.requirements}
    assert by_id["llm-rag"].requirement_type == "required"
    assert by_id["python"].requirement_type == "required"
    # "LangGraph or another agent framework" sits under Nice to have
    assert by_id["langgraph"].requirement_type == "preferred"
    assert by_id["langgraph"].jd_importance < by_id["llm-rag"].jd_importance


def test_a_requirement_always_cites_a_line_from_the_jd():
    parsed = parsed_jd()
    assert parsed.requirements
    for requirement in parsed.requirements:
        assert requirement.evidence, f"{requirement.skill_id} has no JD quote"
        for item in requirement.evidence:
            assert item["quote"] in JD_TEXT or " ".join(item["quote"].split()) in " ".join(JD_TEXT.split())


def test_expected_level_follows_the_words_the_jd_used():
    by_id = {r.skill_id: r for r in parsed_jd().requirements}
    assert by_id["llm-rag"].expected_level == "expert"     # "Production experience building RAG"
    assert by_id["langgraph"].expected_level == "intermediate"


def test_metadata_is_extracted_and_rounds_are_labelled_as_inferred():
    parsed = parsed_jd()
    assert parsed.title and "AI Engineer" in parsed.title
    assert parsed.seniority == "mid"
    assert parsed.min_years_experience == 2
    assert parsed.rounds_inferred is True
    assert "system_design" in parsed.interview_rounds


# ── scoring ───────────────────────────────────────────────────────────────────
def test_priority_is_the_documented_product_of_three_inputs():
    rows = priority.score(parsed_resume(), parsed_jd())
    for row in rows:
        expected = round(row.jd_importance * row.gap * row.interview_relevance, 3)
        assert row.priority == expected
        assert 0 <= row.priority <= 1


def test_bands_follow_the_thresholds():
    assert priority.band(0.55) == "critical"
    assert priority.band(0.549) == "high"
    assert priority.band(0.35) == "high"
    assert priority.band(0.34) == "medium"
    assert priority.band(0.18) == "medium"
    assert priority.band(0.179) == "low"


def test_gap_is_never_negative_and_uses_the_level_scale():
    assert priority.gap("expert", "advanced") == 0.2
    assert priority.gap("advanced", "listed") == 0.5
    assert priority.gap("beginner", "advanced") == 0.0


def test_what_the_jd_wants_beats_what_the_resume_happens_to_list():
    """Skills the resume lists but the JD never mentions are kept for coverage and
    ranked below everything the JD asked for — ENUMS §3 gives them half weight."""
    rows = priority.score(parsed_resume(), parsed_jd())
    jd_only = [r for r in rows if r.in_jd and not r.in_resume]
    resume_only = [r for r in rows if r.in_resume and not r.in_jd]
    assert jd_only, "this JD asks for things the sample resume does not have"
    assert resume_only, "the sample resume lists things this JD never mentions"
    assert min(r.priority for r in jd_only) >= min(r.priority for r in resume_only)
    assert rows[0].in_jd is True
    assert rows[0].priority_band == "critical"


def test_a_resume_claim_never_becomes_a_verified_level():
    rows = priority.score(parsed_resume(), parsed_jd())
    assert all(r.verified_level is None for r in rows)
    assert all(r.status != "verified" for r in rows)


def test_an_assessment_can_raise_a_level_and_shrink_the_gap():
    resume, jd = parsed_resume(), parsed_jd()
    before = {r.skill_id: r for r in priority.score(resume, jd)}
    after = {
        r.skill_id: r
        for r in priority.score(
            resume, jd, verified={"llm-rag": {"level": "advanced", "evidence": [
                {"type": "assessment_answer", "quote": "Measured recall@10 against a labelled set."}]}}
        )
    }
    assert after["llm-rag"].status == "verified"
    assert after["llm-rag"].verified_level == "advanced"
    assert after["llm-rag"].gap < before["llm-rag"].gap
    assert after["llm-rag"].priority < before["llm-rag"].priority


def test_every_row_explains_itself_in_one_sentence():
    rows = priority.score(parsed_resume(), parsed_jd())
    for row in rows:
        assert row.explanation and row.explanation[0].isupper()
        assert len(row.explanation) <= 260


def test_scoring_is_reproducible_byte_for_byte():
    first = json.dumps(build_profile(priority.score(parsed_resume(), parsed_jd())), sort_keys=True)
    second = json.dumps(build_profile(priority.score(parsed_resume(), parsed_jd())), sort_keys=True)
    assert first == second


# ── profile payload ───────────────────────────────────────────────────────────
def test_profile_matches_the_contract_shape_the_ui_reads():
    payload = build_profile(priority.score(parsed_resume(), parsed_jd()))
    assert set(payload) >= {"provisional", "counts", "coverage_by_category", "skills"}
    assert payload["provisional"] is True
    assert set(payload["counts"]) >= {"critical", "high", "medium", "low", "verified", "unverified"}
    assert sum(payload["counts"][k] for k in ("critical", "high", "medium", "low")) == len(payload["skills"])

    required_fields = {
        "skill_id", "name", "category", "status", "claimed_level", "verified_level",
        "expected_level", "confidence", "jd_importance", "interview_relevance", "gap",
        "priority", "priority_band", "explanation", "in_resume", "in_jd", "evidence",
    }
    for skill in payload["skills"]:
        assert set(skill) >= required_fields
        assert skill["evidence"], f"{skill['skill_id']} carries no quote"


def test_coverage_buckets_account_for_every_skill():
    payload = build_profile(priority.score(parsed_resume(), parsed_jd()))
    assert sum(sum((v for k, v in row.items() if k != "category")) for row in payload["coverage_by_category"]) == len(payload["skills"])


def test_skills_are_ordered_by_priority():
    skills = build_profile(priority.score(parsed_resume(), parsed_jd()))["skills"]
    priorities = [s["priority"] for s in skills]
    assert priorities == sorted(priorities, reverse=True)


def test_the_sentence_can_veto_the_section():
    """'Experience with Docker; Kubernetes is a plus' is written in the
    Requirements block but means nice-to-have, and the bar it sets is lower."""
    by_id = {r.skill_id: r for r in parsed_jd().requirements}
    assert by_id["kubernetes"].requirement_type == "preferred"
    assert by_id["kubernetes"].jd_importance < by_id["docker"].jd_importance


def test_strong_experience_is_advanced_not_expert():
    """'strong FastAPI or Flask experience' is a bar, but 'expert' would overstate it."""
    by_id = {r.skill_id: r for r in parsed_jd().requirements}
    assert by_id["flask"].expected_level in {"advanced", "intermediate"}


def test_the_explanation_uses_the_word_the_jd_used():
    rows = {r.skill_id: r for r in priority.score(parsed_resume(), parsed_jd())}
    assert "preferred" in rows["kubernetes"].explanation.lower()
    assert "required" in rows["llm-rag"].explanation.lower()


CONTENT_RESUME = (DATA / "content_resume.txt").read_text()
CONTENT_JD = (DATA / "sample_jd_content.txt").read_text()


def test_a_content_jd_does_not_get_an_engineering_interview_loop():
    """The first version matched the word "design" and gave a content role a
    system-design round. Inventing an interview is worse than saying nothing."""
    parsed = jd_mod.parse(CONTENT_JD)
    assert "system_design" not in parsed.interview_rounds
    assert "coding" not in parsed.interview_rounds
    assert parsed.interview_rounds[:2] == ["portfolio_review", "content_task"]
    assert "analytics_case" in parsed.interview_rounds


def test_the_content_pair_produces_a_ranked_plan():
    resume = resume_mod.parse(extract("resume.txt", CONTENT_RESUME.encode()))
    jd = jd_mod.parse(CONTENT_JD)
    payload = build_profile(priority.score(resume, jd))

    top = payload["skills"][0]
    assert top["priority_band"] == "critical"
    assert top["in_jd"] and top["in_resume"]

    by_id = {s["skill_id"]: s for s in payload["skills"]}
    # the JD asks for SEO and the resume never mentions it: a real, evidenced gap
    assert by_id["seo"]["in_resume"] is False
    assert by_id["seo"]["gap"] > 0.5
    # nothing is verified without an assessment, on either side
    assert all(s["verified_level"] is None for s in payload["skills"])


# ── defects seen on a real JD paste ──────────────────────────────────────────
def test_windows_line_endings_do_not_reach_the_stored_quotes():
    """PowerShell hands over CRLF; a quote ending in \\r looks like corruption and
    breaks exact-string comparisons later."""
    crlf = CONTENT_JD.replace("\n", "\r\n")
    parsed = jd_mod.parse(crlf)
    for requirement in parsed.requirements:
        for item in requirement.evidence:
            assert "\r" not in item["quote"]
            assert item["quote"] == item["quote"].strip()


def test_evidence_is_a_list_of_citations_not_of_matches():
    """The API used to return the same quote twice for one requirement."""
    parsed = jd_mod.parse(CONTENT_JD)
    for requirement in parsed.requirements:
        quotes = [item["quote"] for item in requirement.evidence]
        assert len(quotes) == len(set(quotes))


def test_a_jd_quote_is_labelled_as_a_jd_quote():
    parsed = jd_mod.parse(CONTENT_JD)
    types = {item["type"] for r in parsed.requirements for item in r.evidence}
    assert types == {"jd_requirement"}


def test_role_and_company_are_separated_when_the_title_names_both():
    parsed = jd_mod.parse(CONTENT_JD)
    assert parsed.role == "Content & Social Growth Lead"
    assert parsed.company == "Edoofa"


def test_a_list_item_ending_in_a_semicolon_is_not_chopped():
    text = ("Requirements\n- Newsletter writing and list growth; you have owned a list.\n"
            "- Copywriting across formats.\n")
    parsed = jd_mod.parse(text)
    quotes = [i["quote"] for r in parsed.requirements for i in r.evidence]
    assert any("list growth" in q and len(q) > 30 for q in quotes)


def test_a_plus_phrase_governs_only_its_own_segment():
    """'Experience with Docker; Kubernetes is a plus' — Docker is required, Kubernetes
    is not, and the segment boundary is what tells them apart."""
    parsed = jd_mod.parse(JD_TEXT)
    by_id = {r.skill_id: r for r in parsed.requirements}
    assert by_id["docker"].requirement_type == "required"
    assert by_id["kubernetes"].requirement_type == "preferred"
