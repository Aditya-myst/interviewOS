# Voice interviewer — how it gets built, and what the latency actually is

Nothing here is built yet. This is the plan of record, with the numbers stated up front so
the decision is not made blind. It exists because "add voice" is the step where an
interview product usually starts lying about what it measured — the plan is shaped around
not doing that.

---

## 1. Shape of a spoken turn

```
candidate speaks
   │  MediaRecorder (browser, opus/webm)  ── no plugin, no upload until turn-end
   ▼
Silero VAD  ── energy+model endpointing, fires "they stopped" after ~500 ms of silence
   │
   ├── partial transcripts while they talk (UI shows them live, never scored)
   ▼
final transcript (one API call per turn, not per word)
   │
   ▼
deterministic scoring  ── the existing rubric: quotes + coverage. No LLM decides the score.
   │
   ├── optional LLM follow-up question (one short call, schema-validated)
   ▼
TTS first audio ── interviewer speaks, candidate's mic is muted while it does
```

Two rules that do not bend:

1. **The transcript is the evidence.** Audio never becomes the scored object — the same
   quote-gated rubric that grades typed answers grades spoken ones. If the transcript has
   no quote, the answer does not verify.
2. **The interviewer never talks over the candidate.** Mic is muted from the first
   synthesised phoneme until playback ends; VAD is paused, not merely ignored.

---

## 2. The stack — two options, both free

### Option A — hosted free tier (default, best accuracy)

| Part | Choice | Cost | Why |
|---|---|---|---|
| STT | Groq `whisper-large-v3` | free tier, 2,000 req/day | one call per turn; already have the key |
| VAD | Silero VAD (onnx, in-browser via `@ricky0123/vad-web`) | free, local | no audio leaves the machine to detect silence |
| TTS | browser `speechSynthesis` | free, no key, no quota | starts in ~50–150 ms |
| Follow-ups | Groq `llama-3.1-8b-instant` | free tier | ~300 ms to first token |

Audio uploads only after the turn ends, so nothing streams to a third party while the
candidate is mid-sentence. Recorded audio is discarded after transcription unless the user
opts to keep it.

### Option B — fully local, forever free, no account

| Part | Choice | Footprint | Notes |
|---|---|---|---|
| STT | `faster-whisper` `base.en` or `small.en`, int8 on CTranslate2 | ~150–500 MB, ~1 GB RAM | CPU-only is enough; MIT/Apache weights |
| VAD | Silero VAD | 2 MB | same model as above |
| TTS | **Piper** (`en_US-lessac-medium`) | ~60 MB | runs ~10× real time on one core |
| Follow-ups | local 7B via Ollama, or **no LLM at all** — the rubric already picks the next question | 4–5 GB if used | the interview works without a single generative call |

Option B is the honest answer to "free open source": it needs no key, sends nothing
anywhere, and the whole interview loop still runs if the network dies. It costs accuracy
(see below) and one extra install step.

**Not chosen:** Vapi / ElevenLabs / Deepgram / AssemblyAI. All are per-minute billing, and
none of them improves the thing this product is judged on (whether the score is honest).
Swapping them in later does not change the transcript or scoring schema.

---

## 3. Latency budget

Measured against the target: *candidate stops speaking → interviewer's first sound*.

| Stage | Option A (hosted) | Option B (local, 4 CPU cores) |
|---|---|---|
| Endpointing — 500 ms of silence before the turn is declared over | 0.50 s | 0.50 s |
| Final transcription of a 20 s answer | 0.20–0.50 s | 0.80–1.50 s |
| Score the answer (deterministic rubric, no model) | 0.02 s | 0.02 s |
| Follow-up question, first token (skippable) | 0.30–0.60 s | 0.50–1.50 s |
| First audio out | 0.05–0.15 s | 0.15–0.30 s |
| **Perceived reply latency** | **≈ 1.1 – 1.8 s** | **≈ 2.0 – 3.9 s** |
| Partial transcript appears while speaking | < 0.5 s | 0.6–1.2 s |

Human turn-taking leaves 0.5–1.5 s of silence; Option A lands inside that, Option B is
noticeably slower but still legible as a thoughtful interviewer rather than a broken app.
Both are stated to the user before the first session rather than discovered by them.

If that is not fast enough, in this order:

1. **Drop the follow-up LLM call.** The rubric already knows the next question — that alone
   removes 0.3–1.5 s and removes a hallucination surface.
2. **Act on partials.** Score from the streaming transcript the moment VAD fires, without
   waiting for the final pass; reconcile afterwards.
3. **Shrink the model.** `small.en` → `base.en` → `tiny.en` (roughly halves each stage).
4. **Keep the process warm.** Load the model at session start, never per turn.
5. **Pre-render the interviewer's fixed lines** (greeting, "take your time", "next
   question") to WAV at session start — those turns then cost 0 ms of synthesis.

---

## 4. What is measured, and what is refused

| Claim | Status |
|---|---|
| What the candidate said | **measured** — transcript, quote-gated |
| Whether the answer covers the rubric | **measured** — same scoring as typed |
| Filler-word count, words per minute, longest pause | **measured from the transcript/audio timing**, reported as numbers, never as a grade |
| "Communication score", "confidence", "accent", "fluency" | **refused.** Needs human-rated audio to be meaningful; any number produced here would be invented |

The rehearsal UI therefore shows a **transcript-derived** panel: pace, filler count, pauses
over 3 s — descriptive, not evaluative. Scores still come only from rubric coverage with
quotes, which is what the report already does.

---

## 5. Failure modes the UI must handle before this ships

- **No microphone / denied permission** → visible banner plus a "type the answer instead"
  path that keeps the same session, same scoring.
- **Silence for 30 s** → interviewer prompts once, then offers the typed fallback.
- **Transcription fails or is rate-limited** → the audio is kept in memory, a retry button
  appears, and the turn is marked "not scored" rather than scored on a truncated transcript.
- **Browser without `speechSynthesis`** → text of the question stays on screen; the
  session continues silently.
- **Headphones/echo** → echo cancellation on, and a warning if VAD fires while the
  interviewer is speaking.

---

## 6. Build order (each step schedulable in an hour)

1. Record + upload + transcribe a turn, no voice output — typed answers untouched
2. Silero VAD endpointing + live partials
3. `speechSynthesis` interviewer, mic-mute discipline
4. Transcript-derived pace/filler panel (descriptive numbers only)
5. Piper (Option B) behind a setting, with the same interface
6. Latency instrumentation: log each stage per turn, show the median in `/status`

**Decision needed from you:** Option A (hosted free tier, faster, needs the Groq key) or
Option B (fully local, slower, no account) — or A now with B behind a toggle. Nothing gets
built until you pick.
