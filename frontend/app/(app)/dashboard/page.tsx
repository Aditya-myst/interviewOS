import { Suspense } from "react";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import PageHeader from "@/components/shell/PageHeader";
import IosButton from "@/components/primitives/IosButton";
import ReadinessDial from "@/components/app/ReadinessDial";
import StatTiles, { type Stat } from "@/components/app/StatTiles";
import CoverageStack from "@/components/app/CoverageStack";
import PriorityRow from "@/components/app/PriorityRow";
import InterviewTable from "@/components/app/InterviewTable";
import StateNotice from "@/components/app/StateNotice";
import Skeleton from "@/components/app/Skeleton";
import {
  dashboardFixture,
  parseState,
  type DemoState,
} from "@/lib/fixtures";

export const metadata = { title: "Dashboard — InterviewOS" };

/**
 * The header is static; everything that depends on `?state=` lives behind a
 * Suspense boundary so Cache Components can prerender the shell and stream the
 * body. The fallback IS the loading state — one skeleton, two ways to reach it.
 */
export default function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  const d = dashboardFixture;

  return (
    <div className="max-w-[1180px] mx-auto">
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

      <Suspense fallback={<LoadingState />}>
        <DashboardBody searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function DashboardBody({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  const state: DemoState = parseState((await searchParams).state);

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

      {state === "loading" ? (
        <LoadingState />
      ) : state === "empty" ? (
        <EmptyState />
      ) : (
        <Populated />
      )}

      <p className="mt-8 type-small text-[var(--text-dim)]">
        {state === "empty"
          ? "Nothing to show yet — that is the honest state of a new account."
          : "Data source: contracts/fixtures/dashboard.json · phase 3 renders fixtures, phase 4 swaps in the API."}
      </p>
    </>
  );
}

/* ─── populated ─────────────────────────────────────────────── */
function Populated() {
  const d = dashboardFixture;
  const top = d.priority_skills[0];
  const stats: Stat[] = [
    {
      label: "Verified",
      value: `${d.stats.verified_skills}/${d.stats.skills_total}`,
      tone: d.stats.verified_skills > 0 ? "good" : "default",
    },
    { label: "Interviews", value: String(d.stats.mock_interviews) },
    {
      label: "Topics done",
      value: `${d.stats.topics_done}/${d.stats.topics_total}`,
    },
    {
      label: "Avg score",
      value: d.stats.avg_interview_score ? String(d.stats.avg_interview_score) : "—",
      tone:
        (d.stats.avg_interview_score ?? 0) >= 70
          ? "good"
          : (d.stats.avg_interview_score ?? 0) >= 50
            ? "warn"
            : "default",
    },
  ];

  return (
    <div className="space-y-5">
      {/* Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <section className="card-surface p-6 flex flex-col">
          <p className="type-micro text-[var(--text-dim)] mb-4 m-0">Readiness</p>
          <ReadinessDial
            value={d.readiness}
            label={d.readiness_label}
            provisional={d.provisional}
            className="my-auto"
          />
        </section>

        <section className="card-surface p-6">
          <p className="type-micro text-[var(--text-dim)] mb-4 m-0">This far</p>
          <StatTiles stats={stats} />
        </section>

        {top && (
          <section className="slab-ink p-6 flex flex-col">
            <p className="type-micro text-[var(--on-ink-dim)] m-0 mb-3">
              Start here
            </p>
            <h2 className="type-display-3 text-[var(--on-ink)] m-0 mb-2">
              {top.name}
            </h2>
            <p className="type-small text-[var(--on-ink-dim)] m-0 mb-5">
              {top.explanation}
            </p>
            <div className="mt-auto flex items-center gap-3">
              <IosButton href="/roadmap" variant="primary" size="md" arrow>
                Start this topic
              </IosButton>
              <Link
                href="/gap-map"
                className="type-small text-[var(--on-ink-dim)] hover:text-[var(--on-ink)] underline-offset-4 hover:underline"
              >
                See why
              </Link>
            </div>
          </section>
        )}
      </div>

      {/* Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <section className="lg:col-span-2 card-surface overflow-hidden">
          <div className="flex items-center justify-between gap-4 px-5 py-4 border-b border-[var(--border)]">
            <h2 className="type-h4 m-0">Priority skills</h2>
            <Link
              href="/gap-map"
              className="inline-flex items-center gap-1.5 type-small font-medium text-[var(--brand-strong)] hover:underline underline-offset-4"
            >
              All {d.stats.skills_total} skills
              <ArrowRight size={14} aria-hidden />
            </Link>
          </div>
          {d.priority_skills.map((s) => (
            <PriorityRow key={s.skill_id} skill={s} />
          ))}
        </section>

        <section className="card-surface p-5">
          <h2 className="type-h4 m-0 mb-4">Coverage by category</h2>
          <CoverageStack rows={d.coverage} />
        </section>
      </div>

      {/* Row 3 */}
      <section className="card-surface p-5">
        <div className="flex items-center justify-between gap-4 mb-3">
          <h2 className="type-h4 m-0">Recent mock interviews</h2>
          <span className="type-small text-[var(--text-dim)]">
            Score is transcript-based
          </span>
        </div>
        <InterviewTable interviews={d.interviews} />
      </section>
    </div>
  );
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="card-surface p-6 flex flex-col items-center">
          <Skeleton className="h-3 w-20 self-start mb-6" />
          <Skeleton className="size-[168px] rounded-full" />
          <Skeleton className="h-4 w-28 mt-5" />
          <Skeleton className="h-3 w-40 mt-2" />
        </div>
        <div className="card-surface p-6">
          <Skeleton className="h-3 w-16 mb-6" />
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-[76px]" />
            ))}
          </div>
        </div>
        <div className="card-surface p-6">
          <Skeleton className="h-3 w-24 mb-5" />
          <Skeleton className="h-8 w-40 mb-3" />
          <Skeleton className="h-3 w-full mb-2" />
          <Skeleton className="h-3 w-4/5 mb-6" />
          <Skeleton className="h-11 w-36" />
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card-surface p-5 space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="space-y-2">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-3/4" />
            </div>
          ))}
        </div>
        <div className="card-surface p-5 space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-6" />
          ))}
        </div>
      </div>
    </div>
  );
}
