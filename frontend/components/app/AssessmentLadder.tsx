"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, CircleAlert, RotateCcw } from "lucide-react";
import IosButton from "@/components/primitives/IosButton";
import SkillPill, { type SkillStatus } from "@/components/primitives/SkillPill";
import { startAssessment, submitAssessmentAnswer } from "@/lib/assessment";
import type { AssessmentState } from "../../../contracts/types";
import { cn } from "@/lib/utils";

/**
 * The ladder, on screen.
 *
 * Three checkpoints on one skill, each drawn from a real curriculum subtopic and scored on
 * that subtopic's rubric. What this screen refuses to do:
 *
 *   show a score without the quote that earned it  — a score with no quote is a guess
 *   report a "communication" score                 — there is no audio here
 *   claim the profile changed when it did not      — `persisted: false` says so out loud
 *
 * The question header names the subtopic, because "why am I being asked this" is the
 * first thing a candidate wants to know.
 */
type Phase = "idle" | "asking" | "reviewing" | "done" | "error";

const LEVEL_COPY: Record<string, string> = {
  conceptual: "Start with the concept",
  practical: "Now the mechanics",
  applied: "Now the work itself",
};

export default function AssessmentLadder({
  skillId,
  skillName,
  band,
  status,
}: {
  skillId: string;
  skillName: string;
  band: string;
  status: string;
}) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [state, setState] = useState<AssessmentState | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const boxRef = useRef<HTMLTextAreaElement>(null);

  const words = useMemo(() => answer.trim().split(/\s+/).filter(Boolean).length, [answer]);
  const total = state?.question_total ?? 3;
  const done = state?.answers?.length ?? 0;
  const progress = Math.round((done / Math.max(1, total)) * 100);

  async function begin() {
    setBusy(true);
    setError(null);
    const result = await startAssessment(skillId);
    setBusy(false);
    if (!result.ok) {
      setError(result.message);
      setPhase("error");
      return;
    }
    setState(result.data);
    setPhase("asking");
    requestAnimationFrame(() => boxRef.current?.focus());
  }

  async function send() {
    if (!state || busy || answer.trim().length === 0) return;
    setBusy(true);
    setError(null);
    const result = await submitAssessmentAnswer(state.assessment_id, answer);
    setBusy(false);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setState(result.data);
    setAnswer("");
    setPhase(result.data.status === "completed" ? "done" : "reviewing");
  }

  function next() {
    setPhase("asking");
    requestAnimationFrame(() => boxRef.current?.focus());
  }

  function restart() {
    setState(null);
    setAnswer("");
    setError(null);
    setPhase("idle");
  }

  return (
    <div className="card-surface overflow-hidden">
      <div className="flex flex-wrap items-center gap-3 border-b border-[var(--border)] px-5 py-3">
        <SkillPill label={skillName} status={status as SkillStatus} />
        <span className="type-micro rounded-full border border-[var(--border-strong)] px-2 py-0.5 text-[var(--text-dim)]">
          {band} priority
        </span>
        <span className="ml-auto type-micro text-[var(--text-dim)]">
          {phase === "done"
            ? `${total} of ${total} checkpoints`
            : `checkpoint ${Math.min(done + 1, total)} of ${total}`}
        </span>
        {/* `persisted` is false while the ladder is still running: nothing is written
            until the last checkpoint, so "demo mode" was wrong mid-ladder and alarming at
            the end. The badge now says which of the two it is. */}
        {state?.persisted === false && (
          <span className="type-micro rounded-full bg-[var(--developing)]/10 px-2 py-0.5 text-[var(--developing)]">
            {phase === "done" ? "not saved — the write failed" : "saves when you finish"}
          </span>
        )}
      </div>

      <div className="h-1 w-full bg-[var(--surface-2)]">
        <div
          className="h-full bg-[var(--brand)] transition-[width] duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="p-5 sm:p-7">
        {phase === "idle" && (
          <Intro skillName={skillName} onBegin={begin} busy={busy} />
        )}

        {phase === "error" && (
          <div className="flex items-start gap-3">
            <CircleAlert size={18} className="mt-0.5 text-[var(--weak)]" aria-hidden />
            <div>
              <p className="type-small m-0 text-[var(--text)]">The ladder could not start.</p>
              <p className="type-small m-0 text-[var(--text-dim)]">{error}</p>
            </div>
          </div>
        )}

        {(phase === "asking" || phase === "reviewing") && state?.question && phase === "asking" && (
          <Asking
            state={state}
            answer={answer}
            words={words}
            busy={busy}
            error={error}
            boxRef={boxRef}
            onChange={setAnswer}
            onSubmit={send}
          />
        )}

        {phase === "reviewing" && state && (
          <Reviewing state={state} onNext={next} />
        )}

        {phase === "done" && state?.result && (
          <Result state={state} onRestart={restart} />
        )}
      </div>
    </div>
  );
}

function Intro({
  skillName,
  onBegin,
  busy,
}: {
  skillName: string;
  onBegin: () => void;
  busy: boolean;
}) {
  return (
    <div>
      <p className="type-micro m-0 text-[var(--text-dim)]">Assessment ladder</p>
      <h2 className="type-h3 mt-1 mb-0">Three checkpoints on {skillName}</h2>
      <p className="type-small mt-2 max-w-[62ch] text-[var(--text-dim)]">
        Concept, then mechanics, then the work itself. Each answer is scored against the
        rubric for one subtopic of this skill, and a score needs a sentence to quote — you
        will see both. Three minutes, and the skill stops being a guess.
      </p>
      <ul className="mt-4 grid list-none gap-1.5 p-0">
        {["Conceptual — what it is for", "Practical — how you would do it", "Applied — where you did it"].map(
          (line) => (
            <li key={line} className="type-small flex items-center gap-2 text-[var(--text-dim)]">
              <Check size={14} className="text-[var(--brand-strong)]" aria-hidden />
              {line}
            </li>
          ),
        )}
      </ul>
      <div className="mt-6">
        <IosButton onClick={onBegin} disabled={busy} arrow>
          {busy ? "Starting…" : "Start the ladder"}
        </IosButton>
      </div>
    </div>
  );
}

function Asking({
  state,
  answer,
  words,
  busy,
  error,
  boxRef,
  onChange,
  onSubmit,
}: {
  state: AssessmentState;
  answer: string;
  words: number;
  busy: boolean;
  error: string | null;
  boxRef: React.RefObject<HTMLTextAreaElement | null>;
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  const question = state.question;
  if (!question) return null;
  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="type-micro rounded-full border border-[var(--border-strong)] px-2 py-0.5 text-[var(--text-dim)]">
          {LEVEL_COPY[question.level ?? state.level] ?? "Checkpoint"}
        </span>
        {question.subtopic && (
          <span className="type-micro text-[var(--text-dim)]">rubric: {question.subtopic}</span>
        )}
      </div>

      <p className="mt-3 mb-0 text-[19px] leading-[1.45] font-medium text-[var(--text)]">
        {question.text}
      </p>
      <p className="type-micro mt-2 text-[var(--text-dim)]">
        Scored against {(question.rubric_size ?? 1) > 1 ? `${question.rubric_size} rubric points` : "1 rubric point"}.
        No quote, no credit.
      </p>
      {question.hint && (
        <p className="type-small mt-2 m-0 text-[var(--text-dim)]">{question.hint}</p>
      )}

      <textarea
        id="assessment-answer"
        ref={boxRef}
        value={answer}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
            event.preventDefault();
            onSubmit();
          }
        }}
        rows={5}
        placeholder="What you did, in order, and what changed."
        className="mt-4 w-full resize-y rounded-[12px] border border-[var(--border-strong)] bg-[var(--surface)] px-3.5 py-3 type-small text-[var(--text)] outline-none focus:border-[var(--brand-strong)]"
      />

      {error && <p className="type-small mt-2 m-0 text-[var(--weak)]">{error}</p>}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <IosButton onClick={onSubmit} disabled={busy || answer.trim().length === 0} arrow>
          {busy ? "Scoring…" : "Submit answer"}
        </IosButton>
        <span className="type-micro text-[var(--text-dim)]">
          {words} {words === 1 ? "word" : "words"} · aim for 50+ · ctrl+enter
        </span>
      </div>
    </div>
  );
}

function Reviewing({ state, onNext }: { state: AssessmentState; onNext: () => void }) {
  const last = state.answers?.[state.answers.length - 1];
  const feedback = state.feedback;
  if (!last) return null;
  const score = Math.round(last.score * 100);
  const tone =
    last.status_after === "verified"
      ? "var(--verified)"
      : last.status_after === "developing"
        ? "var(--developing)"
        : "var(--weak)";

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <span
          className="rounded-full px-2.5 py-1 type-micro font-medium"
          style={{ color: tone, background: "color-mix(in srgb, currentColor 12%, transparent)" }}
        >
          {last.status_after.replace("_", " ")}
        </span>
        <span className="font-mono text-[13px] tabular-nums text-[var(--text-dim)]">{score}/100</span>
        <span className="type-micro text-[var(--text-dim)]">checkpoint {last.index} · scored by rubric</span>
      </div>

      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-[var(--surface-2)]">
        <div className="h-full rounded-full" style={{ width: `${score}%`, background: tone }} />
      </div>

      <p className="type-small mt-3 m-0 text-[var(--text)]">{last.why}</p>

      {feedback?.quote && (
        <div className="mt-4 border-l-2 border-[var(--brand-strong)] pl-3">
          <p className="type-micro m-0 text-[var(--text-dim)]">Your evidence, verbatim</p>
          <p className="type-small mt-1 m-0 italic text-[var(--text)]">“{feedback.quote}”</p>
        </div>
      )}

      {!!feedback?.matched?.length && (
        <div className="mt-4">
          <p className="type-micro m-0 text-[var(--text-dim)]">Rubric points you covered</p>
          <ul className="mt-2 flex list-none flex-wrap gap-1.5 p-0">
            {feedback.matched.map((item) => (
              <li
                key={item}
                className="rounded-full bg-[var(--brand)]/12 px-2.5 py-1 type-micro text-[var(--brand-strong)]"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!!feedback?.missing_concepts?.length && (
        <div className="mt-3">
          <p className="type-micro m-0 text-[var(--text-dim)]">Still missing</p>
          <ul className="mt-2 flex list-none flex-wrap gap-1.5 p-0">
            {feedback.missing_concepts.map((item) => (
              <li
                key={item}
                className="rounded-full border border-[var(--border-strong)] px-2.5 py-1 type-micro text-[var(--text-dim)]"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6">
        <IosButton onClick={onNext} arrow>
          Next checkpoint
        </IosButton>
      </div>
    </div>
  );
}

function Result({ state, onRestart }: { state: AssessmentState; onRestart: () => void }) {
  const result = state.result;
  if (!result) return null;
  const verified = result.status_after === "verified";
  const tone = verified ? "var(--verified)" : result.status_after === "developing" ? "var(--developing)" : "var(--weak)";

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <span
          className="rounded-full px-2.5 py-1 type-micro font-medium"
          style={{ color: tone, background: "color-mix(in srgb, currentColor 12%, transparent)" }}
        >
          {result.status_after.replace("_", " ")}
        </span>
        <span className="font-mono text-[13px] tabular-nums text-[var(--text-dim)]">
          level {result.inferred_level} · confidence {Math.round(result.confidence * 100)}%
        </span>
      </div>

      <h3 className="type-h4 mt-3 mb-0">
        {verified
          ? `${state.skill_name} is verified`
          : `${state.skill_name} stays provisional`}
      </h3>
      <p className="type-small mt-2 max-w-[64ch] m-0 text-[var(--text-dim)]">{result.why}</p>

      <ul className="mt-4 grid list-none gap-2 p-0">
        {(state.answers ?? []).map((row) => (
          <li key={row.index} className="flex items-center gap-3">
            <span className="font-mono text-[11px] text-[var(--text-dim)]">0{row.index}</span>
            <span className="type-small flex-1 truncate text-[var(--text-dim)]">{row.level}</span>
            <span className="font-mono text-[12px] tabular-nums text-[var(--text)]">
              {Math.round(row.score * 100)}
            </span>
            <span
              className={cn(
                "w-[110px] text-right type-micro",
                row.score >= 0.75 ? "text-[var(--verified)]" : "text-[var(--text-dim)]",
              )}
            >
              {row.status_after.replace("_", " ")}
            </span>
          </li>
        ))}
      </ul>

      {!!result.redo?.length && (
        <div className="mt-5 rounded-[12px] border border-[var(--border)] p-4">
          <p className="type-micro m-0 text-[var(--text-dim)]">Worth another try</p>
          <p className="type-small mt-1 mb-0 text-[var(--text)]">{result.redo[0].question}</p>
          <p className="type-micro mt-1 mb-0 text-[var(--text-dim)]">
            {result.redo[0].why}
          </p>
        </div>
      )}

      {state.persisted === false && (
        <p className="type-micro mt-4 mb-0 text-[var(--text-dim)]">
          This ladder ran in demo mode: scored honestly, not written to your profile. With a
          database the same run updates the skill and keeps the quotes.
        </p>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <Link
          href="/gap-map"
          className="inline-flex h-11 items-center gap-2 rounded-[12px] bg-[var(--brand)] px-4 text-sm font-semibold text-[var(--ink-950)]"
        >
          See it on the gap map
          <ArrowRight size={15} aria-hidden />
        </Link>
        <IosButton onClick={onRestart} variant="ghost">
          <RotateCcw size={15} aria-hidden /> Run it again
        </IosButton>
      </div>
    </div>
  );
}
