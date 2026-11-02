# Where InterviewOS stands

Last updated: 2026-11-02 · `main` at `78e285d`

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

Backend: **120 tests**, ruff clean, schema checker ("17 queries / 18 tables"). Frontend:
tsc + eslint + `pnpm build` clean.

---

## Provisioned but empty

The database already has `interview_sessions`, `interview_messages`,
`interview_reports`. `contracts/types.ts` already defines `InterviewState`,
`Transcript`, `InterviewReport`. **Nothing writes to them yet.** The one interview
endpoint that exists (`GET /v1/interview/{id}/report`) serves a recorded fixture, not a
live session.

---

## Not built — in the order it will be built

### 1. Interview engine (backend) — next
- `POST /v1/interview/sessions` → session, N questions chosen from priority skills
- question mix from `contracts/types.ts`: `jd` / `resume_project` / `weak_skill` /
  `verified_skill` / `general`, each labelled in the UI with where it came from
- `POST /v1/interview/{id}/answer` → per-answer score **with quote evidence**, no score
  without a quote
- writeback: `candidate_skills` confidence + `status_after`, and `assessment_answers`
- refusal path: an answer with no evidence scores as evidence-free, not as zero

### 2. Interview + report screens
- `/interview`: one question at a time, timer, transcript, "why this question"
- `/report`: overall + per-skill scores, strengths, gaps, weakest answers with a better
  answer outline, next actions. `communication_transcript_based` labelled as
  transcript-only, exactly as the contract says

### 3. Voice interviewer
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

### 4. Assessment ladder
Short checkpoints per subtopic (3–5 items) that flip `provisional: true` skills into
verified ones, so `candidate_skills` has more than one source of truth.

### 5. Tutor chat
Per-skill chat scoped to the candidate's own gaps and the curated resources for that
skill; answers must cite a row or say it does not know.

### 6. LLM extension pass
For the 22 skills with no curated resource: propose a link, verify it with an HTTP
check, mark `generated: true`. A link that fails the check is dropped, not shown.

### 7. Polish that is already known to be missing
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

Days 1–8 are spent (blocks 0–2). Remaining: interview engine → screens → voice →
assessment → tutor → extension pass. Voice is deliberately after the text engine
because it reuses all of it: same session, same scoring, one extra transcription step.
