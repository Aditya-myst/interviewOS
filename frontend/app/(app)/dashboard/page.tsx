import { Suspense } from "react";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import PageHeader from "@/components/shell/PageHeader";
import IosButton from "@/components/primitives/IosButton";
import RadialScore from "@/components/charts/RadialScore";
import Sparkline from "@/components/charts/Sparkline";
import DeltaPill from "@/components/charts/DeltaPill";
import PriorityScatter from "@/components/charts/PriorityScatter";
import CoverageStack from "@/components/app/CoverageStack";
import InterviewTable from "@/components/app/InterviewTable";
import StateNotice from "@/components/app/StateNotice";
import Skeleton from "@/components/app/Skeleton";
import {
  dashboardFixture,
  roadmapFixture,
  skillProfileFixture,
  parseState,
  type DemoState,
} from "@/lib/fixtures";
import type { CandidateSkill } from "../../../../contracts/types";

export const metadata = { title: "Dashboard — InterviewOS" };

type Move = { action: string; meta: string; minutes: number; href: string };

/**
 * The header, the state banner and the trend strip are static; anything that
 * depends on `?state=` sits behind Suspense, which is the shape Cache Components
 * asks for. The fallback IS the loading state.
 */
export default function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  const d = dashboardFixture;

  return (
    <div className="max-w-[1240px] mx-auto">
      <PageHeader
        eyebrow={`Dashboard · ${d.target_role ?? "target role"}`}
        title="Where you stand today"
        actions={
          <>
            <IosButton href="/gap-map" variant="secondary" size="md">
              Review gaps
            </IosButton>
            <IosButton href="/roadmap" variant="primary" size="md" arrow>
              Open roadmap
            </IosButton>
          </>
        }
      />

      <p className="m-0 -mt-4 mb-6 type-small text-[var(--text-dim)]">
        {d.stats.verified_skills} of {d.stats.skills_total} skills verified
        <Sep />
        avg interview score {d.stats.avg_interview_score ?? "—"}
        <Sep />
        {d.stats.topics_done} of {d.stats.topics_total} topics done
        <Sep />
        {d.stats.mock_interviews} mock interviews
      </p>

      <Suspense fallback={<LoadingState />}>
        <DashboardBody searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

function Sep() {
  return <span className="mx-2 text-[var(--border-strong)]" aria-hidden>·</span>;
}

async function DashboardBody({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  const state: DemoState = parseState((await searchParams).state);

  if (state === "loading") return <LoadingState />;
  if (state === "empty") return <EmptyState />;

  return (
    <>
      {state === "degraded" && (
        <div className="mb-5">
          <StateNotice kind="warn" title="Parsing ran in degraded mode">
            The model was unavailable, so this profile came from the
            deterministic parser alone. Every skill below is still real; treat
            the confidence numbers as a floor, not a ceiling.
          </StateNotice>
        </div>
      )}

      <div className="space-y-5">
        <TopRow />
        <NextMoves />
        <section className="card-surface p-5">
          <div className="flex items-center justify-between gap-4 mb-3">
            <h2 className="type-h4 m-0">Recent mock interviews</h2>
            <span className="type-small text-[var(--text-dim)]">
              score is transcript-based
            </span>
          </div>
          <InterviewTable interviews={dashboardFixture.interviews} />
        </section>
      </div>

      <p className="mt-6 type-small text-[var(--text-dim)]">
        Data source: contracts/fixtures/dashboard.json · phase 3 renders
        fixtures, phase 4 swaps in the API.
      </p>
    </>
  );
}

/* ─── readiness · priority map · coverage ───────────────────── */
function TopRow() {
  const d = dashboardFixture;
  const history = d.readiness_history ?? [];
  const values = history.map((h) => h.readiness);
  const delta = values.length > 1 ? values[values.length - 1] - values[0] : 0;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr_300px] gap-5">
      <section className="card-surface p-5 flex flex-col">
        <div className="flex items-start justify-between gap-3">
          <p className="type-micro text-[var(--text-dim)] m-0">Readiness</p>
          {values.length > 1 && <DeltaPill value={delta} suffix=" pts" label="7d" />}
        </div>

        <div className="flex flex-col items-center justify-center flex-1 py-2 gap-3">
          <div className="flex justify-center w-full">
            <RadialScore
              value={d.readiness}
              label={d.readiness_label.replace("_", " ")}
              size={148}
            />
          </div>

          {values.length > 1 && (
            <div className="flex justify-center w-full">
              <Sparkline
                values={values}
                width={184}
                height={38}
                label={`Readiness over the last ${values.length} days`}
              />
            </div>
          )}
        </div>

        <p className="m-0 type-small text-[var(--text-dim)] text-center">
          {d.provisional
            ? "Provisional — partial evidence only"
            : "Based on assessed evidence"}
        </p>
      </section>

      <section className="card-surface p-5">
        <div className="flex items-baseline justify-between gap-4 mb-3">
          <h2 className="type-h4 m-0">Priority map</h2>
          <span className="type-small text-[var(--text-dim)]">
            importance × gap
          </span>
        </div>
        {/* every assessed skill, not just the top three — the shape is the point */}
        <PriorityScatter skills={skillProfileFixture.skills} />
      </section>

      <section className="card-surface p-5">
        <h2 className="type-h4 m-0 mb-4">Coverage</h2>
        <CoverageStack rows={d.coverage} />
      </section>
    </div>
  );
}

/* ─── next three moves, derived, not authored ───────────────── */
function NextMoves() {
  const d = dashboardFixture;
  const skills = [...d.priority_skills].sort((a, b) => b.priority - a.priority);
  const firstRead = roadmapFixture.topics.find(
    (t) => t.status !== "done" && t.resources.some((r) => r.role === "concept")
  );
  const concept = firstRead?.resources.find((r) => r.role === "concept");

  const moves: Move[] = [];

  if (skills[0]) moves.push(assessMove(skills[0]));
  if (firstRead && concept) {
    moves.push({
      action: `Read: ${concept.title}`,
      meta: `${firstRead.title} · concept${concept.provider ? ` · ${concept.provider}` : ""}`,
      minutes: concept.duration_minutes ?? 30,
      href: "/roadmap",
    });
  }
  if (skills[1]) moves.push(assessMove(skills[1]));

  return (
    <section className="card-surface overflow-hidden">
      <div className="flex items-center justify-between gap-4 px-5 py-3 border-b border-[var(--border)]">
        <h2 className="type-h4 m-0">Next three moves</h2>
        <Link
          href="/roadmap"
          className="inline-flex items-center gap-1.5 type-small font-medium text-[var(--brand-strong)] hover:underline underline-offset-4"
        >
          Full roadmap
          <ArrowRight size={14} aria-hidden />
        </Link>
      </div>

      <ol className="list-none m-0 p-0">
        {moves.map((m, i) => (
          <li key={m.action}>
            <Link
              href={m.href}
              className="flex items-center gap-4 px-5 py-3.5 border-b border-[var(--border)] last:border-0 hover:bg-[var(--surface)] transition-colors"
            >
              <span className="font-mono text-[11px] text-[var(--text-dim)] tabular-nums">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block type-small font-medium text-[var(--text)] truncate">
                  {m.action}
                </span>
                <span className="block type-micro text-[var(--text-dim)] mt-0.5 truncate">
                  {m.meta}
                </span>
              </span>
              <span className="shrink-0 type-small text-[var(--text-dim)] tabular-nums">
                {m.minutes} min
              </span>
              <ArrowRight
                size={15}
                className="shrink-0 text-[var(--text-dim)]"
                aria-hidden
              />
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}

function assessMove(skill: CandidateSkill): Move {
  return {
    action: `Assess ${skill.name}`,
    meta: `${skill.priority_band} · ${skill.evidence.length} quote${
      skill.evidence.length === 1 ? "" : "s"
    } on file`,
    minutes: 12,
    href: "/gap-map",
  };
}

/* ─── empty ─────────────────────────────────────────────────── */
function EmptyState() {
  return (
    <section className="card-surface p-8 lg:p-12 text-center">
      <span
        aria-hidden
        className="inline-flex items-center justify-center size-11 rounded-full bg-[var(--brand-soft)] text-[var(--brand-strong)] mb-4"
      >
        <Sparkles size={20} />
      </span>
      <h2 className="type-display-3 m-0 mb-3">Nothing assessed yet</h2>
      <p className="type-body text-[var(--text-dim)] m-0 mb-6 max-w-[52ch] mx-auto">
        Your readiness score is 0 because there is no evidence, not because you
        are unprepared. Upload a resume and a job description and the first
        evaluation takes about four minutes.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <IosButton href="/onboarding" variant="primary" size="lg" arrow>
          Upload resume and JD
        </IosButton>
        <IosButton href="/" variant="secondary" size="lg">
          Back to home
        </IosButton>
      </div>
    </section>
  );
}

/* ─── loading ───────────────────────────────────────────────── */
function LoadingState() {
  return (
    <div className="space-y-5" aria-busy="true" aria-live="polite">
      <span className="sr-only">Loading your dashboard</span>
      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr_300px] gap-5">
        <div className="card-surface p-5 flex flex-col items-center">
          <Skeleton className="h-3 w-20 self-start mb-5" />
          <Skeleton className="size-[148px] rounded-full" />
          <Skeleton className="h-3 w-40 mt-4" />
        </div>
        <div className="card-surface p-5">
          <Skeleton className="h-4 w-32 mb-4" />
          <Skeleton className="h-[230px]" />
        </div>
        <div className="card-surface p-5 space-y-4">
          <Skeleton className="h-4 w-24" />
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-5" />
          ))}
        </div>
      </div>
      <div className="card-surface p-5 space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-10" />
        ))}
      </div>
    </div>
  );
}
