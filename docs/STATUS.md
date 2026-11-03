# Where InterviewOS stands

Last updated: 2026-11-03 · `main` at the upsert-ownership fix

This file is the honest inventory. Anything not marked done does not exist yet — the
UI says "SOON" rather than showing a mock of it.

---

## Done and load-bearing

| Area | What exists | Evidence |
|---|---|---|
| Resume parsing | PDF/DOCX → sections → skills, quotes | `parsing/`, tests |
| JD analysis | paste a JD → role, requirements, importance weights | `parsing/jd.py` |
| Matcher | resume × JD × taxonomy → candidate skill graph | `parsing/matcher.py` |
| Priority engine | gap × JD importance × interview relevance → banded order | `prep/priority.py` |
| Dashboard | readiness ring, priority curve, coverage, next moves | `/dashboard` |
| Gap map | every skill, evidence, band | `/gap-map` |
| Roadmap | ordered topics, prerequisites, real resources | `/roadmap` |
| Curriculum | 41 skills / 137 subtopics, hand-curated | `data/taxonomy.yaml` |
| Resources | 75 links, HTTP-checked, per-subtopic | `data/curated.yaml`, `scripts/check_links.py` |
| Persistence | Supabase: 18 tables, writes on upload + JD | `store.py`, `docs/sql/` |
| Data honesty | every panel states its source (`database` / `fixture`) | `DataSourceBadge` |
| LLM gateway | Groq + Gemini, cached, schema-validated, no-proficiency rule | `llm/` |
| Landing | marketing page, real sample report | `/` |

| Assessment ladder | 3 rungs per skill, curriculum rubrics, consistency-gated verification | `assessment/`, `api/assessment.py` |
| Onboarding | resume upload → JD analysis → parsed skills, requirements and quotes on screen | `/onboarding`, `api/pipeline/[...path]` |
| Tutor | per-skill answers composed from profile rows + curriculum + catalogue, every claim cited | `tutor/`, `api/tutor.py`, `/tutor` |
| Interview engine | sessions, questions from priority skills, quote-gated scoring, report | `interview/`, `api/interview.py` |

Backend: **200 tests**, ruff clean, schema checker ("17 queries / 18 tables"). Frontend:
tsc + eslint + `pnpm build` clean.

---

## Interview engine — done (backend)

Five paths from the spec that already existed, now implemented rather than imagined:
`POST /interview/start` · `POST /interview/answer` · `GET /interview/{id}/transcript` ·
`POST /interview/{id}/evaluate` · `GET /interview/{id}/report`.

- questions are generated from the candidate's **priority skills** and carry a rubric
  built from real subtopic objectives in `data/taxonomy.yaml`
- `source` (jd / resume_project / weak_skill / verified_skill / general) is kept separate
  from `question_type` (fundamentals / advanced / project_deep_dive / …), as the contract
  always intended
- scoring is deterministic and labelled `scored_by: "rubric"`. Coverage of the rubric
  plus a **specificity** check: numbers, first-person actions, a place or time. A fluent
  paragraph that name-drops every keyword scores 0.45 and cannot reach verified
- no quote, no credit: an answer with nothing quotable is capped at 0.25 and flagged
- `evaluate` re-scores from the transcript, so the report is reproducible and auditable
- with a database the session persists and the score is written back to
  `candidate_skills` (confidence moves halfway, one answer is one measurement); without
  one it lives in memory and every report says `persisted: false`

---

## Onboarding — wired to the real pipeline

`/onboarding` used to be a dead button. It now runs the two endpoints that already existed:

1. `POST /v1/resume/upload` (multipart, forwarded byte-for-byte by
   `app/api/pipeline/[...path]/route.ts` so the multipart boundary survives) → parsed
   document, skills, `experience_years`, warnings
2. `POST /v1/jd/analyze {text}` → role, requirements with importance and the JD quote
   that proves each one, then a rescore of the stored resume against the JD

The screen has four states — idle, working (per-step copy), error, done — and the error
state translates API codes into a sentence plus the code in small print
(`pdf_unreadable`, `unsupported_type`, `too_large`, `jd_too_short`, API-unreachable). The
page recovers without a reload: swap the file and press Analyse again.

**What it does not pretend:** with no `DATABASE_URL` the parse is real but nothing is
stored, so the result panel says exactly that, quotes the merge reason from the API, and
offers the dashboard labelled "demo data" rather than a fake redirect to a profile that
does not exist. With a database connected the same panel shows the scored-skill count and
links to `/dashboard` and `/gap-map`. **The persisted branch is not exercised in this
sandbox — there is no Postgres here**; it is the same code path the upload endpoint has
always taken, reviewed but not run.

---

## Fixed after the first real-database run

`POST /v1/resume/upload` returned 500 on a real Supabase project:

```
psycopg.errors.CheckViolation: skill content-strategy: illegal transition weak -> unverified
PL/pgSQL function enforce_skill_transition() line 31 at RAISE
```

**Cause.** The recompute's upsert had `on conflict do update set status = excluded.status`.
The resume/JD pass always computes a *score*, and a fresh score is `unverified` — so every
re-upload tried to reset a skill that an interview had already graded `weak`. The schema's
guard refused the downgrade, correctly, and the exception escaped as a 500.

**The guard was right and the storage layer was wrong.** `status` is verification state,
owned by the assessment and interview paths; the pipeline measures `gap`/`priority`/
`importance` and must not touch it. The fix is in `store.upsert_skills`:

- `status` is no longer in the conflict branch at all — scores still update, verification
  stays put
- `claimed_level` is now `coalesce(...)` like `verified_level`, so a null no longer erases
  what an assessment recorded
- `evidence` is **appended**, not replaced — re-uploading a resume was also deleting the
  assessment quote that justified a verified row, which would have left "verified" with
  nothing behind it

**Second half of the fix: never a 500 for a write the schema refused.** Both pipeline
endpoints catch `SQLAlchemyError` and return `200` with `persisted: false` and
`persist_error: {code: "persist_failed", message: "<one line from the driver>"}` — the parse
is still real and still worth showing. `persisted: true` is now set only *after* the
transaction commits, so a rollback can no longer leave a `resume_id` for a row that is gone.

**Verified against a real PostgreSQL 16.4**, not fixtures: seeded the failing state (a
`weak` skill with an interview quote), ran the upload, and got `200 / persisted: true` with
the skill still `weak`/`beginner`, its assessment evidence intact, and 23 skills scored after
the JD analyse. Zero tracebacks in the API log. Tests: `tests/test_store_upsert.py` (a text
assertion that runs everywhere plus a live-database test gated on
`INTERVIEWOS_TEST_DATABASE_URL`) and `test_a_database_rejection_is_a_stated_failure_not_a_500`.

**Same pass, one more thing the live database exposed:** uploading a second resume left the
first one's skills on the dashboard for ever — a marketing candidate had "LLM & RAG" at the
top of their priority curve. `store.prune_stale_skills` now drops rows the newest resume+JD
no longer mention, but **only** `claimed`/`unverified` ones: a `weak`/`developing`/`verified`
row is evidence someone demonstrated something, and losing the bullet that mentioned it does
not erase that. The merge payload reports `{"scored": 7, "pruned": 1}` so the UI and the logs
can see both numbers.

**Nothing to run in SQL** — the schema was already correct; the fix is application code.

---

## Not built — in the order it will be built

### 1. Interview + report screens — **done**
- `/interview`: one question at a time, progress bar, Ctrl+Enter, live word count,
  feedback panel (score, verbatim quote, covered vs missing rubric points), session
  summary. Questions are ranked by `priority` from the candidate's own profile, so the
  room works for a marketing or a design candidate exactly as it does for an engineer
- `/report`: `?session=<id>` renders the live session; without an id it renders the
  recorded fixture so the screen is reviewable cold. Hero (radial score, role core,
  communication, scored-by), per-skill rows with quotes, weak answers with the outline a
  strong answer would follow, next three moves
- Browsers talk to FastAPI through `app/api/interview/[...path]/route.ts`, a server-side
  proxy, so the API URL never reaches the client and there is no CORS surface. The
  `x-data-source` header decides whether the room says "saved to your account" or
  "not saved — demo mode"
- `communication_transcript_based` is capped at 0.92: a transcript can show someone
  answered at length and in full sentences, and cannot show that they were clear to
  listen to

### 2. Voice interviewer
> Full plan with the latency table: **`docs/VOICE_PLAN.md`**. Not built — waiting on the
> hosted-vs-local decision.

- **Recording:** browser `MediaRecorder` (opus/webm), no plugin
- **Transcription:** Groq `whisper-large-v3` on the existing Groq key (free tier:
  2,000 requests/day), stored as an `interview_message` of role `candidate`, with the
  audio kept local unless the user opts in
- **Interviewer voice:** browser `speechSynthesis` — free, no key, no quota
- **Not using:** Vapi/ElevenLabs/Deepgram (paid per minute). They would be an honest
  upgrade later; the transcript schema does not change if they are swapped in
- **Fully local alternative** (if "free forever, no account, no upload" matters more than
  peak accuracy): `faster-whisper` `base.en`/`small.en` int8 on 4 CPU cores — MIT-ish
  weights, ~1 GB RAM, no network — plus **Silero VAD** for turn-end and **Piper** for the
  interviewer's voice (runs ~10× real time on one core, ~60 MB voice model)

**Latency budget** (the number to hold the design to — candidate stops speaking to
interviewer starts speaking):

| Stage | Hosted (Groq) | Local (faster-whisper + Piper) |
|---|---|---|
| Turn-end: 500 ms of silence after the last word | 0.5 s | 0.5 s |
| Final transcription of a 20 s answer | 0.2–0.5 s | 0.8–1.5 s |
| Score the answer (deterministic rubric, no LLM) | 0.02 s | 0.02 s |
| Optional LLM follow-up, first token | 0.3–0.6 s | 0.5–1.5 s (7B on CPU) |
| First audio out | 0.05–0.15 s (`speechSynthesis`) | 0.15–0.3 s (Piper) |
| **Perceived reply latency** | **~1.1–1.8 s** | **~2.0–3.8 s** |

Both are inside conversational range (humans leave 0.5–1.5 s). Levers if it is too slow:
trust partial transcripts instead of waiting for the final one, shrink the model
(`base.en` → `tiny.en`), keep the process warm so no model load is paid per turn, and
pre-render the fixed interviewer lines to audio at session start.
- **Rule that survives:** a transcript is evidence of what was *said*. Scoring still
  needs a quote. Communication is reported as transcript-derived only — accent, pace
  and confidence are not measured and are not claimed

### 3. Assessment ladder — **done**
- `POST /v1/assessment/start {skill_id}` → three rungs: conceptual, then practical, then
  applied, each drawn from a different subtopic in `data/taxonomy.yaml`
- `POST /v1/assessment/answer {assessment_id, answer}` → graded rung, next rung, or the
  result; `GET /v1/assessment/{id}` resumes
- **The rubric ignores instruction words.** "Use verbs and status codes *correctly*" gives
  rubric points for verbs, status, codes — not for "correctly", which a perfect answer
  never says
- **The score is the ladder's own, and says why.** `0.85 × coverage + 0.15 × concreteness`,
  where coverage is zero without a quotable sentence. The interview's caps (which reward
  measured outcomes) would have pinned a flawless HTTP answer at 0.70, so no ladder could
  ever verify anything
- **Verification needs consistency:** mean ≥ 0.75 *and* no rung below 0.50. One strong
  answer cannot carry a weak one, and the level is conservative — 0.90+ for "expert"
- Screen at `/assessment?skill=<id>`, linked from every gap-map row and from the roadmap's
  empty "Prove it" cells, which used to read "no checkpoint yet — nothing to pass"
- With a database it writes `assessments`, `assessment_answers` and moves
  `candidate_skills` (confidence halfway, verified level, the quoted answer appended to
  `evidence`); without one the response says `persisted: false`

### 4. Tutor chat — **done**
`POST /v1/tutor/ask {question, skill_id?}` → the answer is *composed*, not generated: the
candidate's skill row (levels, band, their own quote), the three most relevant curriculum
subtopics (verbatim objectives from `data/taxonomy.yaml`), and the curated catalogue entries
for those subtopics (free links first, `is_paid` shown). Every claim carries a citation —
a profile row, an evidence quote, a subtopic id or a catalogue URL — and `test_tutor.py`
fails if a focus row arrives without one.

Why no model writes it: asked "how do I get better at RAG", a model produces a confident
course that may not exist. Here an unknown question returns `matched: false` with the reason
and the topics that *can* be answered, and a skill with no catalogue still returns curriculum
steps while saying the links are missing. Deterministic, so it works with no key, no network
and no database — and the same question twice gives the same answer.

Scope resolution: explicit `skill_id` → an alias named in the question → a subtopic's words →
the highest-priority skill on the profile. The last fallback is refused when the question
contains words the skill does not cover, so "what is the salary at Google?" is a refusal, not
the user's own gap dressed up as comprehension.

### 5. LLM extension pass
For the 22 skills with no curated resource: propose a link, verify it with an HTTP
check, mark `generated: true`. A link that fails the check is dropped, not shown.

### 6. Polish that is already known to be missing
- onboarding does not upload yet ("Files stay in this browser until the parsing API
  ships") — wire it to `POST /v1/resume/upload`
- fixture world lacks `missing_roles`, live world shows all three gaps: align
- roadmap is still card-based; a time-budget view (hours per week → dated plan) is
  designed but not built

### Deliberately out of scope for the demo
Multi-user auth (single demo profile, `DEMO_USER_ID`), deployment/CI beyond the build,
mobile app, payments.

---

## The 15-day shape

The engine is done and the loop closes on the backend. Remaining: the two screens that
show it, then voice — which reuses the same session and the same scoring, with one
Transcription step in front. The `audio_url` field already exists in the answer body and
`channel: "voice"` in the start body, because the contract carried them from day one.
