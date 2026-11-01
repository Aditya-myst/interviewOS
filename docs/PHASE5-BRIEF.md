# Phase 5 brief — resume + JD → evidenced skill profile

**Goal:** `/v1/skills/profile` stops reading a fixture and starts reading rows that cite
the user's own document. That is the moment `X-Data-Source` flips from `fixture` to
`database`, and the moment the product's central claim becomes true rather than designed.

## The rule that shapes every step

> A skill may appear in the profile only if it has a `quote` — a literal span from the
> resume or the JD — recorded in `candidate_skills.evidence`. No quote, no row.

The LLM is asked for **structure** (where is the span, which skill does it name), never for
judgement ("rate this 8/10"). Anything it returns without a verbatim span is dropped, and
the drop is logged. Banding (critical/high/medium/low) stays deterministic code so the same
input always produces the same priority.

## Steps, in order

| # | Step | Output | Acceptance |
|---|---|---|---|
| 1 | **Text extraction** — PDF (`pypdf`), DOCX (`python-docx`), plain text; page-anchored so every span maps back to a page | `resumes.raw_text` + page offsets | A 2-page PDF yields offsets that slice back to the original text exactly |
| 2 | **Deterministic skill match** — `data/taxonomy.yaml` aliases + `pg_trgm` fuzzy fallback in Postgres | candidate skills with spans found by string match | Runs with **no LLM at all**; unmatched coverage is measurable |
| 3 | **LLM structure pass** — only for what step 2 could not find, `json_mode`, validated against a pydantic schema | proposals with `quote` fields | A proposal whose quote is not a substring of the document is rejected and logged |
| 4 | **Quote verification gate** — every candidate's `quote` must appear verbatim in `raw_text` | `candidate_skills` rows | Test: a fabricated quote never reaches the database |
| 5 | **JD parse + requirement weighting** — same three steps over the JD, plus must-have/nice-to-have | `jobs.parsed` | Every requirement cites a JD line |
| 6 | **Merge + priority scoring** — resume claim × JD demand × current verification state | `candidate_skills.priority` | Same inputs ⇒ same scores, byte for byte; no LLM in the path |
| 7 | **Flip the route** — `/v1/skills/profile` reads rows, keeps the same JSON shape | `X-Data-Source: database` | Existing frontend renders with zero component changes |

## Deliberately out of scope for Phase 5

- No assessment/question generation yet (that is Phase 6 — the ladder needs a UI to answer in).
- No resource resolution (roadmap step).
- No auth beyond the existing RLS-scoped session; no multi-user upload flow.
- No OCR. A scanned PDF returns an honest `unparseable_document` with the reason.

## Decisions I need from you before step 1

1. **Upload path** — Supabase Storage bucket `resumes` is already provisioned by
   `003_storage.sql`. Send the file through the API (multipart, service key) or have the
   frontend upload straight to Storage and pass the path? *Recommendation: API multipart* —
   one code path, easier to test, and the file never touches the browser's credentials.
2. **PDF library** — `pypdf` (pure Python, no system deps) vs `pdfplumber` (better layout,
   heavier). *Recommendation: `pypdf`*, with `pdfplumber` only if we see column mangling.
   Both are new dependencies, so this one is your call.
3. **Sample documents** — I need one real-ish resume PDF and one job description to test
   against. Yours redacted is ideal; otherwise I'll generate both and label them clearly as
   synthetic test data, never as fixture output.

## Where the repo stands tonight

`main` = `252dd8f`. Frontend, charts, API service, and the verified database
(18/18/22/3/31/100/39, `/dev/db` `ok: true`) are all in. `/v1/*` is fixture-served and
labels itself as such. LLM: Groq primary (`openai/gpt-oss-120b`, ~2.7 s, cached), Gemini
fallback, and a gateway that fails loudly with both reasons rather than inventing an answer.
