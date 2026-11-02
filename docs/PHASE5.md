# Phase 5 — resume + JD → evidenced skill profile

**Status: steps 1–6 of 7 done (uncommitted→committing locally; push blocked on a token).**
Step 7 (persistence + the route flip) is next.

## The rule everything is built around

> A skill may appear in the profile only if it carries a `quote` — a literal span from the
> resume or the JD. No quote, no row.

## What exists now

| # | Step | Where | Verified by |
|---|---|---|---|
| 1 | Text extraction (PDF / DOCX / txt), page-anchored | `app/parsing/extract.py` | 6 tests incl. a hand-built PDF and a DOCX with a table |
| 2 | Deterministic skill match from `data/taxonomy.yaml` | `app/parsing/matcher.py` | 8 tests, incl. weak-alias rejection |
| 3 | Quote gate | `app/parsing/quotes.py` | accepts line wraps, rejects paraphrase and invention |
| 4 | Claim level + confidence (never above "intermediate") | `app/parsing/matcher.py` | 3 tests |
| 5 | JD parse: required vs preferred, expected level, rounds | `app/parsing/jd.py` | 8 tests |
| 6 | Merge + priority scoring | `app/prep/priority.py` | 12 tests, incl. reproducibility |
| 7 | Persist + flip `/v1/skills/profile` | *not built* | — |

**63 tests, no network, no database, no model.** The whole pipeline runs offline:
`python -m app.cli analyze resume.pdf jd.txt`.

## Sample run (the synthetic documents in `backend/tests/data/`)

```
resume: 19 skills · 35 quotes
jd: AI Engineer (LLM Applications) at Northwind Labs · 13 requirements (9 required, 4 preferred)
counts: {'critical': 1, 'high': 1, 'medium': 2, 'low': 19, 'verified': 0, 'unverified': 4}

 # skill           band        prio   gap   jd           you
 1 llm-rag         critical   0.602   0.7 0.86        listed
 2 system-design   high       0.513  0.75 0.72             -
 3 rest-api        medium     0.306   0.5 0.72        listed
 4 docker          medium     0.288   0.5 0.72        listed
 5 flask           low        0.162  0.75 0.72             -
```

`verified: 0` is the honest number: no assessment has run yet, so nothing is verified. The
resume sets `claimed_level` and never `verified_level` — that is a database constraint
(`verified_needs_level`) and a product rule.

## Decisions taken (they were open questions in the brief)

1. **`pypdf` + `python-docx`** for extraction — pure Python, no system dependencies, no
   OCR. A scanned PDF returns `no_text_layer` with a character count instead of pretending.
2. **No LLM in this pass at all.** Taxonomy aliases + section structure cover most of what
   a resume says, and the rest is *measured* (`stats.method` says "deterministic"). The
   model's extension pass comes after step 7 so it has something to be compared against.
3. **`resume_summary` added to `EvidenceType`** (`contracts/ENUMS.md` §5): a skill named
   only in the candidate's summary is a weaker claim than one used in a project, and
   filing it as `resume_project` overstated it.

## Defects the sample document exposed (all fixed, all now tested)

- 4 years of "experience" computed from degree dates `2023 - 2027`.
- `git` claimed from a `github.com/example` contact line.
- A case-insensitive match treated as "capitalised", so "the rest of the team" became
  REST API design.
- "Kubernetes is a plus" inside a Requirements block scored as required.
- "strong experience" scored as expert.
- The explanation sentence hardcoded "Required" for preferred requirements.

## Next: step 7

- `POST /v1/resume/upload` (multipart) → extract → parse → write `resumes` row
- `POST /v1/jd/analyze` → write `job_descriptions` row
- upsert `candidate_skills` (unique on `user_id, skill_id`) with evidence jsonb
- `/v1/skills/profile` reads rows when present, fixtures otherwise, and says which in
  `X-Data-Source`
- one migration-free addition: nothing — the schema already has every column this needs
