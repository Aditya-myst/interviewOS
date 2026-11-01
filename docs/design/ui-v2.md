# UI v2 — less prose, more shape

## The diagnosis

The current app screens are honest and readable, and that is the problem: every
screen is a single column of cards where each fact is a sentence. Nine skills
means nine paragraphs. A recruiter scanning for ten seconds learns "someone
wrote a lot", not "this person is 42% ready and the RAG gap dominates".

Three specific faults:

1. **Every row carries a paragraph.** The `explanation` sentence is the product's
   best idea and the worst thing to repeat nine times at 14px. It belongs one
   click away, or in the one row that matters.
2. **No chart answers the screen's question.** "Where do I stand?" is answered by
   text and a number. It should be answered by a shape you can read in a glance.
3. **Uniform density.** Header, cards, table, footer all at the same weight —
   nothing tells the eye where to land first.

## The rules

- **One hero visual per screen.** If a screen has three equal cards, it has no
  answer.
- **Captions, not paragraphs.** One line under a number, 12–14px. Anything longer
  goes behind a disclosure or a side sheet.
- **Progressive disclosure everywhere.** Row → quote. Topic → resources. Score →
  rubric. The first view is a map; the detail is one click deep.
- **No new chart dependency.** recharts is already there for the radar; the rest
  are hand-built SVG because they are 30–60 lines each and we control the type
  and the colour tokens exactly.
- **Every chart has a text equivalent** (`sr-only` table) and respects
  `prefers-reduced-motion` (draw-on-view becomes instant).

## Chart inventory (build once, reuse)

| component | what it is | where |
|---|---|---|
| `RadialScore` | one ring, value + label, draws on mount | dashboard readiness, topic progress |
| `Sparkline` | 7–14 point trend, no axes | readiness over time |
| `PriorityScatter` | x = gap, y = JD importance, r = interview relevance, colour = band | dashboard hero |
| `SkillMatrix` | 9 rows × 3 columns of tinted cells (importance / evidence / recency) | gap map hero |
| `CoverageBars` | stacked per-category bars (already exists) | dashboard side |
| `TopicRail` | vertical timeline with per-topic ring and status dot | roadmap hero |
| `ScoreRadar` | competency radar from the report | interview report |
| `DeltaPill` | ±N with arrow, capped colour | everywhere a change exists |

## Dashboard

```
┌ Where you stand today ──────────────────── AI Engineer · 4 days to interview ┐
│                                                                              │
│   ◎ 42%        PRIORITY × GAP                    COVERAGE                    │
│   Early        ┌──────────────────────────┐      AI      ▓▓▒░░  0/3          │
│   ▲ +6 this    │        ● LLM & RAG       │      Backend ▒▒▒░░  0/1         │
│     week       │                          │      Data    ▓▓▓▓▒  1/2         │
│   ▁▂▃▅▆ 7d     │   ● FastAPI              │      Infra   ░░░░░  0/1         │
│                │        ● System Design   │      Lang    ▓▓▓▓▓  1/1         │
│                └──────────────────────────┘                                   │
│                 gap →                   9 skills · 2 verified                │
├──────────────────────────────────────────────────────────────────────────────┤
│ NEXT 3 MOVES (one line each, no paragraphs)                                  │
│  1  Assess LLM & RAG        critical · 2 quotes on file     12 min  →       │
│  2  Read: RAG evaluation    concept · checked 2 days ago    40 min  →       │
│  3  Assess FastAPI          high · resume claim unproven    10 min  →       │
└──────────────────────────────────────────────────────────────────────────────┘
```

- The scatter replaces the priority card list. Position *is* the explanation: top
  right = important and missing. Hover/tap shows the skill name; click opens the
  row.
- The explanation sentence appears only in the expanded row and in the gap map.
- Recent interviews collapse into a 3-row strip with a sparkline of scores.

## Gap map

```
┌ 9 skills, 2 verified ──────────────────────────── filter: [All 9][Crit 1][High 2]… ┐
│  SKILL MATRIX (importance × evidence × recency)                                     │
│                    JD importance   Evidence   Recency                               │
│  LLM & RAG         ████████        ▓▓▒░       3d                                    │
│  FastAPI           ███████         ░░░░       3d                                    │
│  System Design     ██████          ░░░░       —                                     │
│  …                                                                                  │
│  click any row → side sheet: status, why, quotes, "start assessment"                │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

The matrix replaces the 6-column table as the *first* thing on the screen; the
table survives below it as the sortable, dense view for people who want it. Text
per row drops from ~20 words to ~4, with the paragraph moving into the sheet.

## Roadmap

```
┌ What to study, in order ───────────────────────────────────────── 1/5 · 20% ┐
│                                                                             │
│  ①─●  Evaluating a RAG pipeline         deep dive   ●●●◐○   120 min        │
│  │    3 resources · 2 checked today                        [open ▼]        │
│  ②─○  Dependency injection & testing    core         ○○○○○    90 min        │
│  │                                                                          │
│  ③─○  Designing an LLM service          core         ○○○○○   150 min        │
└─────────────────────────────────────────────────────────────────────────────┘
```

Rail, not cards. Each topic expands in place to show the triplet:

```
  LEARN            PRACTISE                    PROVE
  [docs]   →       [repo / exercise]     →     [checkpoint]
  FastAPI —        Full Stack FastAPI          (not resolved yet —
  Dependencies     Template test suite         labelled search)
  ✓ checked 1d     ✓ checked 1d
```

The "why" sentence becomes the caption under each resource, capped at one line
(`text-clamp-2`), with the provider and check timestamp as micro type.

## Text budget per screen

| screen | prose allowed above the fold |
|---|---|
| dashboard | 1 lead line + 3 next-move rows (≤ 12 words each) |
| gap map | 1 lead line; explanations only in the sheet |
| roadmap | 1 summary sentence + per-resource 1-line why |
| report | scores + 3 strengths + 3 gaps; prose only inside each gap |

## Motion

Numbers count up once (`CountUp`, already built). Charts draw on first view via
`IntersectionObserver`, and are static under `prefers-reduced-motion`. No
parallax on app screens — motion on an app screen is a signal, not decoration.

## Build order

1. `components/charts/*` — RadialScore, Sparkline, PriorityScatter, SkillMatrix,
   TopicRail (+ sr-only tables). Nothing else can be laid out until these exist.
2. Dashboard re-layout on top of them; delete the priority card list and the
   separate stat tiles.
3. Gap map: matrix above, table below, side sheet for one skill.
4. Roadmap: rail + in-place expansion.
5. Report and interview screens get the same treatment when they exist.

Each step ends with 1440/390 screenshots and a link crawl, same as every other
phase.
