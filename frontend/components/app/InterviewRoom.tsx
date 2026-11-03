"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, CircleAlert, Mic2, RotateCcw, Sparkles } from "lucide-react";
import IosButton from "@/components/primitives/IosButton";
import SkillPill, { type SkillStatus } from "@/components/primitives/SkillPill";
import type { InterviewFeedback, InterviewReport, InterviewState } from "@/lib/interview";
import { startInterview, submitAnswer } from "@/lib/interview";
import { cn } from "@/lib/utils";

const SOURCE_LABEL: Record<string, string> = {
  jd: "from the job description",
  resume_project: "from a project on your resume",
  weak_skill: "from your weakest required skill",
  verified_skill: "a harder probe on something you already proved",
  general: "a general question on this skill",
};

const STATUS_COPY: Record<string, string> = {
  verified: "Verified — this is now evidence on your profile.",
  developing: "Developing — right direction, not enough proof yet.",
  weak: "Weak — thin evidence, prepare a concrete example.",
  needs_revision: "Needs revision — nothing here could be scored.",
};

type Phase = "idle" | "asking" | "reviewing" | "done" | "error";

export default function InterviewRoom({
  role,
  coverage,
  skills,
  questionCount,
}: {
  role: string;
  coverage: { skill: string; band: string }[];
  skills: number;
  questionCount: number;
}) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [state, setState] = useState<InterviewState | null>(null);
  const [feedback, setFeedback] = useState<InterviewFeedback | null>(null);
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<string>("unknown");
  const boxRef = useRef<HTMLTextAreaElement>(null);

  const words = useMemo(() => answer.trim().split(/\s+/).filter(Boolean).length, [answer]);
  const progress = state ? Math.round((state.asked / Math.max(1, state.total)) * 100) : 0;

  async function begin() {
    setBusy(true);
    setError(null);
    const result = await startInterview(questionCount);
    setBusy(false);
    if (!result.ok) {
      setError(result.message);
      setPhase("error");
      return;
    }
    setState(result.data);
    setSource(result.source);
    setFeedback(null);
    setPhase("asking");
    requestAnimationFrame(() => boxRef.current?.focus());
  }

  async function send() {
    if (!state || busy || answer.trim().length === 0) return;
    setBusy(true);
    setError(null);
    const result = await submitAnswer(state.session_id, answer);
    setBusy(false);
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setFeedback(result.data.feedback);
    setState(result.data.state);
    setReport(result.data.report ?? null);
    setSource(result.source);
    setPhase(result.data.state.status === "completed" ? "done" : "reviewing");
  }

  function next() {
    setFeedback(null);
    setAnswer("");
    setPhase("asking");
    requestAnimationFrame(() => boxRef.current?.focus());
  }

  function restart() {
    setPhase("idle");
    setState(null);
    setFeedback(null);
    setReport(null);
    setAnswer("");
    setError(null);
  }

  /* ───────────────────────────── idle ───────────────────────────── */
  if (phase === "idle") {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
        <section className="card-surface p-6 sm:p-8">
          <p className="type-micro text-[var(--text-dim)] m-0">Mock interview</p>
          <h2 className="mt-2 mb-3 text-[30px] leading-[1.1] font-semibold tracking-[-0.02em]">
            {questionCount} questions on what this role actually asks for.
          </h2>
          <p className="type-small text-[var(--text-dim)] max-w-[60ch] m-0">
            Questions are generated from your own priority skills for{" "}
            <strong className="text-[var(--text)]">{role}</strong> and scored against a
            rubric built from the curriculum. Every score needs a quote from your answer —
            so a fluent answer with no example cannot pass here.
          </p>

          <ul className="mt-6 grid gap-2 list-none p-0">
            {[
              "Answer in your own words. Type it as you would say it out loud.",
              "Name the situation, what you did, and what changed because of you.",
              "A number beats an adjective. “22% to 41%” is evidence; “significantly” is not.",
            ].map((line, index) => (
              <li key={line} className="flex gap-3 type-small text-[var(--text-dim)]">
                <span className="mt-0.5 font-mono text-[11px] text-[var(--brand-strong)]">
                  0{index + 1}
                </span>
                {line}
              </li>
            ))}
          </ul>

          <div className="mt-7 flex items-center gap-3">
            <IosButton onClick={begin} loading={busy} size="lg" arrow>
              Start the interview
            </IosButton>
            <span className="type-micro text-[var(--text-dim)]">
              about {Math.max(6, questionCount * 3)} minutes
            </span>
          </div>

          {error && (
            <p className="mt-4 flex items-start gap-2 type-small text-[var(--weak)]">
              <CircleAlert size={16} className="mt-0.5 shrink-0" aria-hidden />
              {error}
            </p>
          )}
        </section>

        <aside className="card-surface p-6">
          <p className="type-micro text-[var(--text-dim)] m-0">What it will ask about</p>
          <p className="type-small text-[var(--text-dim)] mt-2">
            The {Math.min(coverage.length, questionCount)} highest-priority skills in your profile.
          </p>
          <ol className="mt-4 grid gap-2 list-none p-0">
            {coverage.slice(0, questionCount).map((row, index) => (
              <li key={row.skill} className="flex items-baseline gap-3">
                <span className="font-mono text-[11px] tabular-nums text-[var(--text-dim)]">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="type-small text-[var(--text)]">{row.skill}</span>
                <span className="ml-auto type-micro uppercase tracking-[0.08em] text-[var(--text-dim)]">
                  {row.band}
                </span>
              </li>
            ))}
          </ol>
          <p className="mt-5 pt-4 border-t border-[var(--border)] type-micro text-[var(--text-dim)]">
            {skills} skills in your graph. Nothing here is generic: each question carries the
            rubric it will be scored against.
          </p>
        </aside>
      </div>
    );
  }

  /* ───────────────────────────── error ──────────────────────────── */
  if (phase === "error") {
    return (
      <section className="card-surface p-8 text-center">
        <CircleAlert className="mx-auto text-[var(--weak)]" aria-hidden />
        <h2 className="mt-3 text-[22px] font-semibold">The interview service is not answering</h2>
        <p className="mt-2 type-small text-[var(--text-dim)]">{error}</p>
        <div className="mt-5 flex justify-center gap-3">
          <IosButton onClick={begin} variant="secondary" arrow>
            Try again
          </IosButton>
          <IosButton href="/dashboard" variant="ghost">
            Back to dashboard
          </IosButton>
        </div>
      </section>
    );
  }

  /* ───────────────────────── session / report ───────────────────── */
  const question = state?.question;

  return (
    <div className="grid gap-6">
      <section className="card-surface overflow-hidden">
        <div className="flex flex-wrap items-center gap-3 border-b border-[var(--border)] px-5 py-3">
          <span className="inline-flex items-center gap-1.5 type-micro text-[var(--text-dim)]">
            <Mic2 size={13} aria-hidden /> {role}
          </span>
          <span className="type-micro text-[var(--text-dim)]">
            question {Math.min((state?.asked ?? 0) + 1, state?.total ?? questionCount)} of{" "}
            {state?.total ?? questionCount}
          </span>
          <span
            className={cn(
              "ml-auto rounded-full px-2 py-0.5 type-micro",
              source === "database"
                ? "bg-[var(--brand)]/12 text-[var(--brand-strong)]"
                : "bg-[var(--surface-2)] text-[var(--text-dim)]",
            )}
            title={
              source === "database"
                ? "Session row written to Postgres"
                : "Session lives in memory for this demo and will not survive a restart"
            }
          >
            {source === "database" ? "saved to your account" : "not saved — demo mode"}
          </span>
        </div>
        <div className="h-1 w-full bg-[var(--surface-2)]">
          <div
            className="h-full bg-[var(--brand)] transition-[width] duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>

        <div className="p-5 sm:p-7">
          {phase === "asking" && question && (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <SkillPill label={question.skill_name ?? "Skill"} status="claimed" />
                <span className="type-micro text-[var(--text-dim)]">
                  {SOURCE_LABEL[question.source ?? "general"] ?? question.source}
                </span>
              </div>
              <h2 className="mt-4 mb-0 text-[24px] leading-[1.25] font-semibold tracking-[-0.01em] max-w-[70ch]">
                {question.text}
              </h2>
              <p className="mt-3 type-micro text-[var(--text-dim)]">
                Scored against {question.rubric_size ?? 3} rubric points. No quote, no credit.
              </p>

              <label htmlFor="answer" className="sr-only">
                Your answer
              </label>
              <textarea
                id="answer"
                ref={boxRef}
                value={answer}
                onChange={(event) => setAnswer(event.target.value)}
                onKeyDown={(event) => {
                  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") send();
                }}
                rows={7}
                placeholder="Situation, what you did, what changed. Numbers if you have them."
                className="mt-4 w-full resize-y rounded-[14px] border border-[var(--border-strong)] bg-[var(--surface)] p-4 type-small leading-[1.6] outline-none focus-visible:outline-2 focus-visible:outline-[var(--brand-strong)]"
              />
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <IosButton onClick={send} loading={busy} disabled={words < 5} arrow>
                  Submit answer
                </IosButton>
                <span className="type-micro text-[var(--text-dim)]">
                  {words} words {words < 25 ? "· aim for 60+" : "· good"} · Ctrl+Enter
                </span>
              </div>
              {error && (
                <p className="mt-3 flex items-start gap-2 type-small text-[var(--weak)]">
                  <CircleAlert size={16} className="mt-0.5 shrink-0" aria-hidden /> {error}
                </p>
              )}
            </>
          )}

          {(phase === "reviewing" || phase === "done") && feedback && (
            <FeedbackPanel
              feedback={feedback}
              done={phase === "done"}
              sessionId={state?.session_id ?? ""}
              onNext={next}
              onRestart={restart}
            />
          )}
        </div>
      </section>

      {phase === "done" && report && <SessionSummary report={report} onRestart={restart} />}
    </div>
  );
}

/* ────────────────────────────── feedback ──────────────────────────── */

function FeedbackPanel({
  feedback,
  done,
  sessionId,
  onNext,
  onRestart,
}: {
  feedback: InterviewFeedback;
  done: boolean;
  sessionId: string;
  onNext: () => void;
  onRestart: () => void;
}) {
  const pct = Math.round(feedback.score * 100);
  const tone =
    feedback.status_after === "verified"
      ? "var(--verified)"
      : feedback.status_after === "developing"
        ? "var(--developing)"
        : "var(--weak)";

  return (
    <div>
      <div className="flex flex-wrap items-center gap-3">
        <span
          className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 type-micro font-semibold"
          style={{ background: `color-mix(in oklab, ${tone} 12%, transparent)`, color: tone }}
        >
          {feedback.status_after === "verified" ? <Check size={13} aria-hidden /> : null}
          {feedback.status_after.replace("_", " ")}
        </span>
        <span className="font-mono text-[13px] tabular-nums text-[var(--text-dim)]">
          {pct}/100
        </span>
        <span className="type-micro text-[var(--text-dim)]">
          scored by {feedback.scored_by ?? "rubric"} · {feedback.skill_name}
        </span>
      </div>

      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-[var(--surface-2)]">
        <div
          className="h-full rounded-full transition-[width] duration-700"
          style={{ width: `${pct}%`, background: tone }}
        />
      </div>

      <p className="mt-4 type-small text-[var(--text)] m-0">{STATUS_COPY[feedback.status_after]}</p>
      <p className="mt-1 type-small text-[var(--text-dim)] m-0">{feedback.why}</p>

      {feedback.quote ? (
        <blockquote className="mt-5 border-l-2 border-[var(--brand-strong)] pl-4 m-0">
          <p className="type-micro text-[var(--text-dim)] m-0">Your evidence, verbatim</p>
          <p className="type-small italic text-[var(--text)] mt-1 mb-0">“{feedback.quote}”</p>
        </blockquote>
      ) : (
        <p className="mt-5 flex items-start gap-2 type-small text-[var(--weak)]">
          <CircleAlert size={16} className="mt-0.5 shrink-0" aria-hidden />
          Nothing in that answer could be quoted as evidence, so it earned no credit — that
          is the rule, not a scoring accident.
        </p>
      )}

      {feedback.matched.length > 0 && (
        <div className="mt-5">
          <p className="type-micro text-[var(--text-dim)] m-0">Rubric points you covered</p>
          <ul className="mt-2 flex flex-wrap gap-1.5 list-none p-0">
            {feedback.matched.map((item) => (
              <li
                key={item}
                className="rounded-full bg-[var(--brand)]/12 px-2.5 py-1 type-micro text-[var(--brand-strong)]"
              >
                {item.replace(/-/g, " ")}
              </li>
            ))}
          </ul>
        </div>
      )}

      {feedback.missing.length > 0 && (
        <div className="mt-3">
          <p className="type-micro text-[var(--text-dim)] m-0">Still missing</p>
          <ul className="mt-2 flex flex-wrap gap-1.5 list-none p-0">
            {feedback.missing.map((item) => (
              <li
                key={item}
                className="rounded-full border border-[var(--border-strong)] px-2.5 py-1 type-micro text-[var(--text-dim)]"
              >
                {item.replace(/-/g, " ")}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-3">
        {done ? (
          <>
            <IosButton href={`/report?session=${sessionId}`} arrow>
              Open the full report
            </IosButton>
            <IosButton onClick={onRestart} variant="ghost">
              <RotateCcw size={15} aria-hidden /> Start over
            </IosButton>
          </>
        ) : (
          <IosButton onClick={onNext} arrow>
            Next question
          </IosButton>
        )}
      </div>
    </div>
  );
}

/* ─────────────────────────── session summary ──────────────────────── */

function SessionSummary({ report, onRestart }: { report: InterviewReport; onRestart: () => void }) {
  const overall = Math.round((report.overall_scores.overall ?? 0) * 100);
  return (
    <section className="ink-slab rounded-[18px] p-6 sm:p-7">
      <div className="flex flex-wrap items-center gap-4">
        <div>
          <p className="type-micro text-[var(--text-dim)] m-0">Session finished</p>
          <p className="mt-1 mb-0 text-[34px] font-semibold leading-none tabular-nums text-[var(--text)]">
            {overall}
            <span className="text-[16px] font-normal text-[var(--text-dim)]">/100</span>
          </p>
        </div>
        <p className="type-small text-[var(--text-dim)] max-w-[52ch] m-0">
          {report.strengths[0]}
        </p>
        <div className="ml-auto flex gap-2">
          <IosButton href="/report" variant="secondary" arrow>
            Report
          </IosButton>
          <IosButton onClick={onRestart} variant="ghost">
            <Sparkles size={15} aria-hidden /> Again
          </IosButton>
        </div>
      </div>
      <ul className="mt-5 flex flex-wrap gap-x-6 gap-y-2 list-none p-0">
        {report.per_skill.map((row) => (
          <li key={row.skill_id} className="flex items-center gap-2">
            <SkillPill label={row.name} status={row.status_after as SkillStatus} />
            <span className="font-mono text-[12px] tabular-nums text-[var(--text-dim)]">
              {Math.round(row.score * 100)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/* Keeps the Link import used when the report link is swapped for a custom element. */
export const __internal = { Link, ArrowRight };
