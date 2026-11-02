# InterviewOS — Shared Enums (single source of truth)

Every builder (backend, UI, prompts) uses these exact strings. A typo here is a bug in both layers.

## 1. SkillStatus — the skill state machine
| value | meaning | UI colour token |
|---|---|---|
| `claimed` | Appears in the resume, nothing verified yet | `--unverified` |
| `unverified` | In the JD, no evidence at all (not in resume) | `--unverified` |
| `weak` | Assessed; significant gaps demonstrated | `--weak` |
| `developing` | Learning in progress, partial evidence | `--developing` |
| `verified` | Demonstrated at the JD's expected level | `--verified` |
| `needs_revision` | Previously verified, evidence is stale | `--verified` + dashed border, hollow dot |

Legal transitions:
```
claimed        -> weak | developing | verified      (only via assessment evidence)
unverified     -> weak | developing | verified
weak           -> developing | verified
developing     -> verified | weak
verified       -> needs_revision                    (after stale window or failed interview)
needs_revision -> developing | verified
```
Rule: **no transition without an `Evidence` record.** A status change with no evidence is a bug.

## 2. Level — proficiency scale
`none` (0) . `listed` (1) . `beginner` (1) . `intermediate` (2) . `advanced` (3) . `expert` (4)

`listed` means "named on the resume, no proof": same numeric value as `beginner`, displayed differently.
`verified_level` may never exceed what the rubric evidence supports. The resume never sets `verified_level`.

## 3. PriorityBand
`critical` . `high` . `medium` . `low`

`priority = jd_importance x gap x interview_relevance` (each 0..1)
bands: `>=0.55 critical`, `>=0.35 high`, `>=0.18 medium`, else `low`

## 4. RequirementType
`required` . `preferred`

## 5. EvidenceType
`resume_skill_list` . `resume_project` . `resume_experience` . `resume_summary` . `assessment_answer` . `interview_answer` . `user_correction`

`jd_requirement` was also added in Phase 5: a requirement's quote comes from the job
description, and filing it as `resume_skill_list` claimed the candidate had written it.
Both directions of evidence sit in the same list, so the type is what tells you which
document the quote came from.

`resume_summary` was added in Phase 5: a skill named only in the candidate's own summary
is a claim about themselves with no work behind it, and filing it as `resume_project`
would have overstated it. The four `resume_*` types are ranked by strength —
`resume_project`/`resume_experience` (used somewhere) > `resume_skill_list` (listed) >
`resume_summary` (asserted).

### Interview rounds
`technical` . `coding` . `system_design` . `take_home` . `behavioral` . `hr` .
`portfolio_review` . `content_task` . `analytics_case`

The last three were added in Phase 5: a content or growth role is not interviewed with a
system-design round, and reporting one would have been a fabrication dressed as inference.

## 6. AssessmentLevel
`conceptual` . `practical` . `applied`   (the 3-rung ladder per skill)

## 7. QuestionType
`fundamentals` . `advanced` . `coding` . `debugging` . `project_deep_dive` . `scenario` . `system_design` . `behavioral`

## 8. InterviewMode
`beginner_practice` . `intermediate_technical` . `advanced_technical` . `resume_based` . `jd_based` . `full_mock`

## 9. Channel
`text` . `voice`

## 10. ResourceRole
`concept` . `practice` . `checkpoint` — every learning topic resolves to exactly one of each, or a labelled gap. Never a fabricated link.

## 11. ParseStatus
`ok` . `degraded` — `degraded` = model unavailable, deterministic-only parse. UI shows a banner and keeps working.

## 12. Error codes
`not_found` . `bad_input` . `unauthenticated` . `invalid_token` . `unsupported_file` . `file_too_large` .
`parse_failed` . `llm_unavailable` . `quota_exceeded` . `degraded_mode` . `insufficient_evidence`

Error envelope (every non-2xx):
```json
{ "error": { "code": "bad_input", "message": "Human readable", "detail": "optional" } }
```

## 13. Priority explanation contract
Every skill row includes `explanation`: one server-generated sentence, no template gaps.
Example: `"Required in the JD at intermediate level; your resume only lists it, so evidence is unverified -> critical."`
The UI renders it verbatim and never rewords or recomputes it.
