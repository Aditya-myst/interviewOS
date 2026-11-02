# InterviewOS — Architecture

**One line:** a preparation system that measures what a candidate can *demonstrate* against what a target job *requires*, then teaches only the gaps that will actually be asked.

**The differentiator is not the chatbot.** It is the evidence pipeline: resume claims, JD requirements and assessment evidence are reconciled into a per-skill state machine that can justify every priority it emits.

---

## 1. Stack (₹0 tier, open source where it matters)

| Layer | Choice | Why | Free limit to design around |
|---|---|---|---|
| UI | Next.js 15 App Router, TS, Tailwind, shadcn/ui, recharts | Types generated from the contract; components are copied in, not vendored | — |
| API | FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic | Validation-first, structured outputs | — |
| Agents | LangGraph (StateGraph only) + Postgres checkpointer | Controlled flow, resumable assessments | — |
| LLM primary | Gemini Flash (API) | Best free quality/latency | ~1,500 req/day, 15 RPM → needs cache |
| LLM fallback | Groq (open-weight Qwen/Llama/Kimi) | Keeps the "open models" story, 0 local compute | 30 RPM, ~1,000 req/day |
| Embeddings | `fastembed` + bge-small-en-v1.5, local ONNX | No key, no quota, ~300 MB RAM | CPU burst only, cached |
| PDF | `pypdf` → `pdfplumber` → `docling` (fallback) | MIT/BSD, no AGPL in the dependency tree | — |
| Matching | `pyahocorasick` + `rapidfuzz` + `taxonomy.yaml` | Deterministic, auditable, free | — |
| DB | Supabase Postgres + pgvector | Managed, RLS, free tier | 500 MB |
| Auth | Supabase Auth | Free 50k MAU | — |
| Search | `ddgs` (dev) / SearXNG (prod VM) | No paid search API | ddgs is rate-limited, cache it |
| Content APIs | YouTube Data, GitHub REST, arXiv, official docs | Structured, stable | ~100 YT searches/day total |
| Voice | Groq Whisper (STT) + Kokoro/Piper (TTS) + MediaRecorder | Fully free, no Vapi | 2,000 audio req/day |
| Jobs | FastAPI BackgroundTasks + `jobs` table | No Redis on day 1 | — |
| Eval | pytest + promptfoo + golden corpus | Repeatable, not vibes | — |
| Deploy | Vercel Hobby + Render free (or Oracle always-free VM) | $0 | Render sleeps after 15 min |

**No Ollama.** Local inference was removed: it needed 5–7 GB RAM on an 8 GB laptop and produced sustained heat for a capability nothing in the product depends on. The offline claim is now supported by the deterministic parser instead.

---

## 2. System shape

```
Next.js (all fetch via lib/api.ts, types from contracts/)
        │  JWT (Supabase)
        ▼
FastAPI monolith
  api/        resumes · jds · skills · assessments · learning · interviews · analytics
  agents/     resume · jd · assessor · gap · tutor · questions · interviewer · evaluator
  workflows/  preparation_graph · interview_graph            (LangGraph, checkpointed)
  services/   pdf · taxonomy · llm_gateway · llm_cache · resources · scoring · jobs
        │
        ├── Postgres (Supabase): 17 tables + pgvector
        ├── LLM gateway: Gemini → Groq  (+ llm_cache, prompt-hash keyed)
        ├── Resource resolver: curated.yaml → docs → free curricula → GitHub → YouTube → ddgs
        └── Voice: MediaRecorder → Whisper → interviewer → Kokoro TTS
```

Two LangGraph workflows, everything else is CRUD around them:

1. **Preparation**: `ingest → parse_resume → parse_jd → canonicalise → match → gap_score → roadmap → resolve_resources → persist`
2. **Interview**: `select_targets → generate_questions → conduct(adaptive) → evaluate(rubric) → write_back(candidate_skills)`

Rule: **every LLM call returns a Pydantic model.** No raw model text reaches the database.

---

## 3. Parsing (resume and JD)

Hybrid, deterministic-first. The LLM normalises; it is never the source of truth.

| Stage | What happens | Why |
|---|---|---|
| 1 Extract | `pypdf`; if <300 chars → `pdfplumber`; if image-only → `docling`/tesseract. Keep char offsets. | Enables evidence highlighting |
| 2 Normalise | NFKC, de-ligature, de-bullet, rejoin hyphen breaks, preserve offset map | Aho-Corasick needs clean text |
| 3 Segment | Rule-based headers (font/size from pdfplumber) → sections; LLM only for odd layouts | Cheap, deterministic |
| 4 Candidate match | `pyahocorasick` over `taxonomy.yaml` aliases, ±120 char context | High recall, zero cost |
| 5 LLM extraction | Schema-constrained JSON: skills with **verbatim** `evidence_quote`, projects, years, unsupported claims | Structured, validatable |
| 6 Reconcile | No quote → **drop** (hallucination guard). Deterministic hit the LLM missed → **add** (recall guard). `rapidfuzz` canonicalises | Both error directions covered |
| 7 Persist | Pydantic validation → one repair retry → else deterministic-only with `parse_status=degraded` | Demo never dies |

**Claimed level** comes only from explicit signals (years, "expert", skill bars, project scope); otherwise `listed`. `verified_level` can never be set by parsing — only by assessment evidence.

**Confidence**: `0.20 base + 0.30 project/experience evidence + 0.20 two or more mentions + 0.15 recency + 0.15 years`, capped at **0.80**. Nothing from the resume is ever "verified".

**JD specifics**: per-bullet tiering (`required` vs `preferred` from cue words), `expected_level` from seniority/years, mention counts, and `interview_rounds` inferred from text — always labelled `rounds_inferred: true` ("inferred, not company-confirmed").

---

## 4. Skill state machine and priority

```
claimed → weak | developing | verified
unverified → weak | developing | verified
weak → developing | verified
developing → verified | weak
verified → needs_revision
needs_revision → developing | verified
```
No transition without an `Evidence` row. A status change with no evidence is a bug.

```
effective = verified_level if evidence else min(claimed, listed+1) × 0.6
gap       = clamp(expected − effective, 0, 4) / 4
priority  = jd_importance × gap × interview_relevance      (all 0..1)
bands: ≥0.55 critical · ≥0.35 high · ≥0.18 medium · else low
```
Every row stores the three factors **and** a server-generated `explanation` sentence. The UI renders it verbatim; it never recomputes or rewords it.

---

## 5. Learning-resource resolver

The rule that keeps this honest: **you do not search for resources — you resolve subtopics against a curated graph, then verify what you find.**

1. **Subtopics are curated.** `data/taxonomy.yaml` holds 41 skills / 137 subtopics with objectives and levels. The tutor walks this graph instead of inventing a syllabus.
2. **Trust-ordered ladder**: `curated.yaml` (T0) → official docs slug templates (T1) → free curricula — freeCodeCamp, roadmap.sh, Kaggle Learn, MIT OCW (T2) → GitHub search (T3) → YouTube Data API (T4) → `ddgs`/SearXNG (T5) → labelled search URL, never a fabricated link (T6).
3. **Verify**: httpx GET (not HEAD), follow redirects, require 200, reject login walls, detect paid platforms, extract title/duration.
4. **Score**: `0.45·cosine(subtopic, resource via bge-small) + 0.20·authority + 0.15·level match + 0.10·engagement + 0.10·freshness`.
5. **Rerank**: one LLM call over the top 12 picks **1 concept + 1 practice + 1 checkpoint** (matching the teaching loop). Hard guard: any returned URL must be string-identical to a candidate, else rejected.
6. **Cache**: selections keyed by `(subtopic, level)` for 90 days; nightly link-check job marks dead links stale.

Cost per prep plan on free tiers: one rerank per skill, one embedding batch, 0–2 searches — and only for subtopics nobody has resolved before.

---

## 6. Data model (17 tables)

`profiles` · `resumes` · `job_descriptions` · `skills` · `skill_subtopics` · `candidate_skills` ·
`assessments` · `assessment_answers` · `learning_paths` · `learning_topics` · `resources` ·
`topic_resources` · `resource_checks` · `interview_sessions` · `interview_messages` ·
`interview_reports` · `llm_cache` · `jobs`

Design notes:
- `candidate_skills` is the heart: status, claimed/verified level, confidence, the three priority factors, priority, band, evidence JSON, `last_assessed_at`, and a unique `(user_id, skill_id)`.
- `resources` keyed by URL (unique) so link health is shared across users; `topic_resources` carries role + score.
- `llm_cache` keyed by `sha256(model + prompt + schema_version)` — cuts quota use, makes demos instant, kills 429 risk on cached paths.
- RLS on every user-facing table; `service_role` key never leaves the backend.

---

## 7. Decisions worth defending (ADRs)

| # | Decision | Alternative rejected | Reason |
|---|---|---|---|
| 1 | Modular monolith | microservices | 15 days, one deploy, no network failure surface |
| 2 | LangGraph state machine, not autonomous agents | free-running multi-agent chat | reliability; a bad JD parse must not silently propagate |
| 3 | Deterministic-first parsing + LLM normaliser | "dump PDF into LLM" | auditable, cheaper, survives model outage |
| 4 | Evidence required for every status change | single LLM proficiency label | explains *why*, prevents fake expertise |
| 5 | Curated subtopic graph + verified resources | free-form web search per question | no hallucinated links, stable curricula |
| 6 | URL-allowlist guard on rerank | trust the model's URLs | fabricated links are the #1 trust killer in tutor demos |
| 7 | No Ollama / no local inference | local 7B model | 8 GB laptop, heat, zero product dependency |
| 8 | `llm_cache` from day 1 | add caching later | free-tier quota is the binding constraint |
| 9 | Text interviews before voice | voice-first | voice is 1 day of integration on top of a working evaluator |
| 10 | Fixtures before endpoints | API-first UI | two builders can't invent each other's fields |

---

## 8. Non-goals (deliberately cut)

Multi-tenant orgs · payments · resume builder · job scraping · autonomous agents · real-time voice coaching ·
emotion or delivery analysis · microservices/Kubernetes · RAG over arbitrary user PDFs.

One honesty rule: any "communication" score is labelled **transcript-based**. We do not measure delivery.

---

## 9. Demo-safety rules

1. Golden-path outputs are pre-warmed in `llm_cache`; the demo never depends on a live model call.
2. Every screen has `?state=empty|loading|error|degraded` so resilience is shown, not claimed.
3. `degraded` mode is a *feature*: the deterministic parser still produces a full gap analysis.
4. Warm the API (and DB) ten minutes before presenting — Render free sleeps.

---

## 10. Evaluation plan (Day 12)

| What | Corpus | Metric | Pass bar |
|---|---|---|---|
| Resume parsing | 50 resumes, 20 hand-labelled | skill recall / precision, quote validity | recall ≥0.90, precision ≥0.85, 100% quotes verbatim |
| JD tiering | 30 JDs | required/preferred accuracy | ≥0.85 |
| Assessment consistency | 20 answers graded twice + 10 hand-graded | level agreement | ≥80% within one level |
| Question relevance | 30 generated questions | rubric-graded relevance to JD | ≥0.8 |
| Resource links | 200 resolved | live, free, level-appropriate | 100% live, no fabricated URLs |
| Roadmap quality | 10 plans | human review checklist | ≥8/10 sensible ordering |

Numbers go in the README. "It works" is not a claim; a precision number is.
