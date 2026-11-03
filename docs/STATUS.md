# Where InterviewOS stands

Last updated: 2026-11-02 · `main` at the interview-engine commit

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
| Interview engine | sessions, questions from priority skills, quote-gated scoring, report | `interview/`, `api/interview.py` |

Backend: **141 tests**, ruff clean, schema checker ("17 queries / 18 tables"). Frontend:
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
- **Recording:** browser `MediaRecorder` (opus/webm), no plugin
- **Transcription:** Groq `whisper-large-v3` on the existing Groq key (free tier:
  2,000 requests/day), stored as an `interview_message` of role `candidate`, with the
  audio kept local unless the user opts in
- **Interviewer voice:** browser `speechSynthesis` — free, no key, no quota
- **Not using:** Vapi/ElevenLabs/Deepgram (paid per minute). They would be an honest
  upgrade later; the transcript schema does not change if they are swapped in
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

### 4. Tutor chat
Per-skill chat scoped to the candidate's own gaps and the curated resources for that
skill; answers must cite a row or say it does not know.

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
