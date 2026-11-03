import { Suspense } from "react";
import Link from "next/link";
import DataSourceBadge from "@/components/app/DataSourceBadge";
import Skeleton from "@/components/app/Skeleton";
import RadialScore from "@/components/charts/RadialScore";
import IosButton from "@/components/primitives/IosButton";
import SkillPill, { type SkillStatus } from "@/components/primitives/SkillPill";
import { loadInterviewReport } from "@/lib/api";

export const metadata = { title: "Interview report — InterviewOS" };

/**
 * The API's reason strings are written for the per-skill row, where there is room to
 * be complete: "LLM & RAG: Nothing in the answer touched the rubric for this question,
 * so it cannot be scored as evidence. Answer with a specific example you actually
 * worked on." Printed four times down the page that reads as a scolding, so the hero
 * and the redo list get the short form and the full sentence stays in "By skill".
 */
function compactReason(text: string): string {
  return text
    .replace(/\s*Answer with a specific example[^.]*\./i, "")
    .replace(
      /Nothing in the answer touched the rubric for this question,?\s*so it cannot be scored as evidence\./i,
      "No quotable evidence"
    )
    .replace(/\s+/g, " ")
    .trim();
}



/**
 * The report.
 *
 * Two ways in, and it never pretends otherwise:
 *
 *   ?session=<id>  a session that just ended — live, scored from that transcript
 *   no session     the recorded fixture, so the screen is reviewable before anyone
 *                  has taken an interview
 *
 * `communication_transcript_based` is shown as what it is: a transcript measurement.
 * Accent, pace and confidence are not measured here and the page says so, because a
 * product that claims to read confidence from text is lying to the candidate.
 */
export default async function ReportPage({
  searchParams,
}: {
  searchParams: Promise<{ session?: string }>;
}) {
  return (
    <Suspense fallback={<Skeleton className="h-[420px] w-full" />}>
      <ReportBody searchParams={searchParams} />
    </Suspense>
  );
}

async function ReportBody({
  searchParams,
}: {
  searchParams: Promise<{ session?: string }>;
}) {
  const { session } = await searchParams;
  const payload = await loadInterviewReport(session ?? "latest");
  const report = payload.data;
  const live = Boolean(session) && payload.source !== "unreachable";

  const overall = Math.round((report.overall_scores.overall ?? 0) * 100);
  const core = report.overall_scores.technical;
  const comms = report.overall_scores.communication_transcript_based;
  const verified = report.per_skill.filter((row) => row.status_after === "verified").length;

  return (
    <div className="grid gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="type-micro text-[var(--text-dim)] m-0">Report</p>
          <h1 className="mt-1 mb-0 text-[30px] font-semibold leading-tight tracking-[-0.02em]">
            {live ? "How that session scored" : "A recorded session, start to finish"}
          </h1>
          <p className="mt-1 type-small text-[var(--text-dim)] m-0 max-w-[70ch]">
            {live
              ? "Built from the transcript you just produced. Every score below has a quote behind it."
              : "No session in hand, so this is a recorded run kept as a fixture — useful to see the shape of the output, not a claim about you."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <IosButton href="/interview" variant="secondary" arrow>
            Take an interview
          </IosButton>
          <DataSourceBadge
            source={payload.source}
            reason={payload.reason}
            endpoint={payload.endpoint}
          />
        </div>
      </header>

      {report.persisted === false && (
        <p className="rounded-[12px] border border-[var(--border-strong)] bg-[var(--surface-2)] px-4 py-3 type-small text-[var(--text-dim)] m-0">
          This session ran in demo mode: it was scored correctly but not written to the
          database, so it will not survive a restart. With Supabase configured the same run
          saves to <code className="font-mono text-[12px]">interview_reports</code> and updates
          your skill graph.
        </p>
      )}

      {/* ── hero ─────────────────────────────────────────────────────── */}
      <section className="card-surface overflow-hidden">
        <div className="grid grid-cols-1 md:grid-cols-[220px_1fr] divide-y md:divide-y-0 md:divide-x divide-[var(--border)]">
          <div className="p-6 flex flex-col items-center justify-center gap-3">
            <RadialScore
              value={overall}
              label="session score"
              size={150}
              tone={overall >= 70 ? "brand" : overall >= 45 ? "developing" : "weak"}
            />
            <p className="type-micro text-[var(--text-dim)] m-0 text-center">
              {verified} of {report.per_skill.length} skills verified
            </p>
          </div>

          <div className="p-6 grid gap-5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Stat
                label="Role core"
                value={core == null ? "—" : `${Math.round(core * 100)}`}
                hint="your three most-required skills"
              />
              <Stat
                label="Communication"
                value={comms == null ? "—" : `${Math.round(comms * 100)}`}
                hint="from the transcript only — no accent, pace or confidence"
              />
              <Stat
                label="Scored by"
                value={report.scored_by ?? "rubric"}
                hint="deterministic rubric, reproducible"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <p className="type-micro text-[var(--text-dim)] m-0">What held up</p>
                <ul className="mt-2 grid gap-1.5 list-none p-0">
                  {report.strengths.slice(0, 3).map((line) => (
                    <li key={line} className="type-small text-[var(--text)]">
                      {line}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="type-micro text-[var(--text-dim)] m-0">What did not</p>
                <ul className="mt-2 grid gap-1.5 list-none p-0">
                  {(report.gaps.length ? report.gaps : ["Nothing scored weak this session."])
                    .slice(0, 3)
                    .map((line) => (
                      <li key={line} className="type-small text-[var(--text-dim)]">
                        {compactReason(line)}
                      </li>
                    ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── per skill ────────────────────────────────────────────────── */}
      <section className="card-surface overflow-hidden">
        <div className="flex items-center justify-between gap-3 px-5 py-3 border-b border-[var(--border)]">
          <h2 className="text-[15px] font-semibold m-0">By skill</h2>
          <span className="type-micro text-[var(--text-dim)]">
            score, evidence and what it means
          </span>
        </div>
        <ul className="list-none p-0 m-0 divide-y divide-[var(--border)]">
          {report.per_skill.map((row) => (
            <li key={row.skill_id} className="px-5 py-4 grid gap-2">
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-semibold type-small text-[var(--text)]">{row.name}</span>
                <SkillPill label={row.status_after.replace("_", " ")} status={row.status_after as SkillStatus} />
                <span className="ml-auto font-mono text-[12px] tabular-nums text-[var(--text-dim)]">
                  {Math.round(row.score * 100)}/100
                </span>
              </div>
              <div className="h-1 w-full overflow-hidden rounded-full bg-[var(--surface-2)]">
                <div
                  className="h-full rounded-full bg-[var(--brand)]"
                  style={{ width: `${Math.round(row.score * 100)}%` }}
                />
              </div>
              <p className="type-small text-[var(--text-dim)] m-0">{row.comment}</p>
              {row.quote && (
                <p className="type-small italic text-[var(--text)] m-0 border-l-2 border-[var(--brand-strong)] pl-3">
                  “{row.quote}”
                </p>
              )}
            </li>
          ))}
        </ul>
      </section>

      {/* ── weak answers + next actions ──────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.15fr_1fr] gap-6">
        <section className="card-surface p-5">
          <h2 className="text-[15px] font-semibold m-0">The answers to redo</h2>
          <p className="type-micro text-[var(--text-dim)] mt-1">
            Each one comes with the outline a strong answer would follow.
          </p>
          <ol className="mt-4 grid gap-4 list-none p-0">
            {(report.weak_answers ?? []).map((item, index) => (
              <li key={item.question} className="border-t border-[var(--border)] pt-3 first:border-0 first:pt-0">
                <div className="flex gap-3">
                  <span className="font-mono text-[11px] text-[var(--brand-strong)] mt-0.5">
                    0{index + 1}
                  </span>
                  <div>
                    <p className="type-small font-medium text-[var(--text)] m-0">{item.question}</p>
                    <p className="type-micro text-[var(--text-dim)] mt-1 mb-0">
                      {compactReason(item.why_weak)}
                      {item.score != null && ` · ${Math.round(item.score * 100)}/100`}
                    </p>
                    <ul className="mt-2 grid gap-1 list-none p-0">
                      {item.better_answer_outline.map((step) => (
                        <li key={step} className="type-small text-[var(--text-dim)] flex gap-2">
                          <span aria-hidden className="text-[var(--brand-strong)]">
                            —
                          </span>
                          {step}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </li>
            ))}
            {!report.weak_answers?.length && (
              <li className="type-small text-[var(--text-dim)]">
                Nothing scored below 50 in this session.
              </li>
            )}
          </ol>
        </section>

        <section className="ink-slab rounded-[18px] p-5">
          <h2 className="text-[15px] font-semibold m-0 text-[var(--text)]">Next three moves</h2>
          <ol className="mt-4 grid gap-3 list-none p-0">
            {report.next_actions.slice(0, 3).map((action, index) => (
              <li key={action} className="flex gap-3 type-small text-[var(--text-dim)]">
                <span className="font-mono text-[11px] text-[var(--brand-strong)] mt-0.5">
                  0{index + 1}
                </span>
                {action}
              </li>
            ))}
          </ol>
          <div className="mt-5 flex flex-wrap gap-2">
            <IosButton href="/roadmap" variant="secondary" size="sm" arrow>
              Open roadmap
            </IosButton>
            <Link
              href="/gap-map"
              className="inline-flex items-center type-small text-[var(--text-dim)] underline-offset-4 hover:underline"
            >
              see every skill
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div>
      <p className="type-micro text-[var(--text-dim)] m-0">{label}</p>
      <p className="mt-1 mb-0 font-mono text-[22px] leading-none tabular-nums text-[var(--text)]">
        {value}
      </p>
      <p className="mt-1 type-micro text-[var(--text-dim)] m-0">{hint}</p>
    </div>
  );
}
