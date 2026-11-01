# The agent, concretely

Two sentences that decide everything else:

1. **The pipeline is a state machine, not a conversation.** Parsing → gaps →
   priorities → assessment → roadmap. Every step has typed input, typed output,
   and a failure path. Nothing "decides" to skip a step.
2. **The LLM is a component inside a step, never the step itself.** Where a rule
   can do the job, a rule does the job. The LLM is used for exactly four things:
   reading messy text, writing questions, evaluating free-text answers, and
   rewriting a candidate resource list. All four have a non-LLM fallback.

This is why the demo survives a model outage: everything except question
generation and grading has a deterministic path.

---

## 1. The graph

```
                     ┌──────────────┐
  resume bytes ─────▶│ 1 ingest     │  deterministic (pypdf / mammoth / tesseract)
  JD text      ─────▶└──────┬───────┘
                            ▼
                     ┌──────────────┐
                     │ 2 segment    │  deterministic (headings, bullets, sections)
                     └──────┬───────┘
                            ▼
        ┌───────────────────┴────────────────────┐
        ▼                                        ▼
 ┌──────────────┐                        ┌──────────────┐
 │ 3a skill     │  Aho-Corasick alias    │ 3b jd parse  │  matcher + LLM for
 │    extract   │  match over taxonomy   │              │  required/preferred
 └──────┬───────┘  + LLM for leftovers   └──────┬───────┘  and expected level
        │      each skill MUST carry a quote    │
        └───────────────────┬────────────────────┘
                            ▼
                     ┌──────────────┐
                     │ 4 merge      │  candidate_skills upsert (status claimed/unverified)
                     └──────┬───────┘
                            ▼
                     ┌──────────────┐
                     │ 5 priority   │  DETERMINISTIC: jd_importance x gap x relevance
                     │              │  + server-written explanation sentence
                     └──────┬───────┘
                            ▼
                     ┌──────────────┐
                     │ 6 assess     │  LLM writes 2-4 questions per skill from the
                     │   ladder     │  subtopic graph; rubric anchors per level
                     └──────┬───────┘
                            ▼
                     ┌──────────────┐
                     │ 7 evidence   │  LLM grades each answer against the rubric,
                     │   gate       │  capped: verified_level <= evidence supports
                     └──────┬───────┘
                            ▼
                     ┌──────────────┐
                     │ 8 resolve    │  deterministic ladder + HTTP check + embedding
                     │   resources  │  score; LLM only reranks 12 candidates
                     └──────┬───────┘
                            ▼
                     ┌──────────────┐
                     │ 9 compose    │  DETERMINISTIC ordering by priority + prereqs
                     │   roadmap    │  + server-written summary
                     └──────┬───────┘
                            ▼
                   learning_paths + learning_topics + topic_resources
```

Then two dialogue surfaces hang off that result:

```
  topic ──▶ tutor (teach / ask / check) ──▶ checkpoint ──▶ status writeback
  plan  ──▶ interviewer (question / follow-up / close) ──▶ report ──▶ writeback
```

## 2. Node by node

| # | node | LLM? | output contract | failure path |
|---|---|---|---|---|
| 1 | ingest | no | text + page count | unsupported file → `unsupported_file`; scanned PDF → OCR, else `parse_failed` |
| 2 | segment | no | sections[] with char offsets | no headings → treat whole doc as one section |
| 3a | skill extract | **partly** | `ExtractedSkill[]`, each with `evidence[].quote` + offsets | matcher-only; fewer skills, `parse_status=degraded` |
| 3b | JD parse | **partly** | `JDRequirement[]` with `requirement_type`, `expected_level` | matcher-only, `expected_level` inferred from years mentioned |
| 4 | merge | no | `candidate_skills` rows | — |
| 5 | priority | no | `priority`, `priority_band`, `explanation` | — (pure function, unit-testable) |
| 6 | assess | **yes** | 2–4 `{question, question_type, rubric}` per skill | template questions from subtopic objectives, marked `degraded` |
| 7 | gate | **yes** | `inferred_level`, `status_after`, `confidence`, evidence | deterministic keyword rubric; never promotes above `developing` |
| 8 | resolve | **partly** | `topic_resources` | curated-only, no rerank |
| 9 | compose | no | `learning_paths`, `learning_topics`, summary | — |

**Rule that is not negotiable:** the LLM never writes `status`, `verified_level`
or `priority`. It proposes evidence; a deterministic function converts evidence
into levels; the database trigger refuses a status change with no evidence.

## 3. State object

One Pydantic model threaded through the graph, checkpointed between nodes:

```python
class PlanState(BaseModel):
    run_id: str
    user_id: str
    resume_id: str | None
    jd_id: str | None
    parse_status: Literal["ok", "degraded"] = "ok"
    sections: list[Section] = []
    resume_skills: list[ExtractedSkill] = []
    jd_requirements: list[JDRequirement] = []
    skills: list[CandidateSkill] = []
    assessments: list[AssessmentSpec] = []
    topics: list[TopicSpec] = []
    warnings: list[str] = []          # surfaced in the UI banner, never swallowed
    llm_calls: int = 0
    model_chain: list[str] = []       # which provider answered, in order
```

`warnings` and `model_chain` are user-visible on purpose: a demo where you can
point at "the fallback model answered this call" is stronger than one where you
claim it never happens.

## 4. Model routing and budget

- Primary: **Gemini 2.5 Flash** (free tier). Fallback: **Groq** open-weight.
- Ordering: cache → primary → fallback → deterministic path → explicit error.
- Cache key: `sha256(model + canonical_prompt + schema_version)`, 90-day TTL.
  Stored in `llm_cache`, service-role only, because prompts contain resume text.
- Every call requests a JSON schema and is validated with Pydantic before use.
  A validation failure counts as a provider failure, not a "retry harder".
- Hard budget per plan: **≤ 9 LLM calls**. Typical: 2 extract, 3–4 assessment
  generation (batched per skill group), 1 grading pass, 1 rerank, 0–2 extras.
  At 15 RPM that is one preparation plan in well under a minute.

Embeddings are **not** a runtime model. The 100 subtopics and curated resources
are embedded once, offline, and the vectors are seeded into Postgres. Similarity
is then a SQL `<=>` query. That is why nothing on the laptop has to run a model.

## 5. What the agent is forbidden to do

| forbidden | why | enforced by |
|---|---|---|
| assert proficiency with no quote | the entire product claim | `ExtractedSkill.evidence` required at validation; DB trigger on status change |
| invent a URL | dead links are the thing we criticise | rerank output URL must be string-identical to a candidate, else dropped |
| write its own status transition | self-graded progress is worthless | `enforce_skill_transition()` trigger |
| score "communication" from audio | we only ever see the transcript | field named `communication_transcript_based`, UI labels it |
| claim a level above the rubric | inflation makes the score meaningless | `verified_level = min(rubric_supported, expected_level)` |
| silently degrade | a demo that lies about its state is a bug | `parse_status` + `warnings[]` rendered in a banner |

## 6. Where LangGraph is used, and where it is not

- **Used** for the assessment ladder and the tutor/interview loops: these need a
  checkpointer, resumability (a user closes the tab mid-assessment) and explicit
  edges for "not enough evidence yet".
- **Not used** for ingest → segment → priority → compose. Those are pure
  functions with no branching worth a graph runtime; a graph there is ceremony,
  and ceremony is what makes 15-day projects late.

## 7. Demo script this design makes possible

1. Upload a real resume + a real JD (Northwind Labs posting, or any live one).
2. Show the quote behind the first extracted skill.
3. Kill the model key, re-run: banner says `degraded`, the plan still appears.
4. Show a priority row's explanation, then the three factors behind it.
5. Open a topic, show the *verified* resource with its check timestamp.
6. Answer three assessment questions, watch a status move `claimed → weak →
   developing` with the new evidence attached.
