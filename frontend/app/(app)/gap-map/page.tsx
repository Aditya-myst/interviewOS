import { Suspense } from "react";
import Link from "next/link";
import { ArrowRight, ScanSearch } from "lucide-react";
import PageHeader from "@/components/shell/PageHeader";
import IosButton from "@/components/primitives/IosButton";
import GapMapTable from "@/components/app/GapMapTable";
import SkillMatrix from "@/components/charts/SkillMatrix";
import StateNotice from "@/components/app/StateNotice";
import DataSourceBadge from "@/components/app/DataSourceBadge";
import Skeleton from "@/components/app/Skeleton";
import { loadSkillProfile } from "@/lib/api";
import { parseState } from "@/lib/fixtures";

export const metadata = { title: "Gap map — InterviewOS" };

/**
 * The gap map reads `/v1/skills/profile`. When that endpoint serves rows the
 * matrix is this user's evidence; when it serves its fixture the badge says so.
 * Either way the page renders a real shape — an empty skill list is the empty
 * state, never a blank card that looks finished.
 */
export default function GapMapPage({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  return (
    <div className="max-w-[1180px] mx-auto">
      <Suspense fallback={<GapMapLoading />}>
        <GapMapBody searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function GapMapBody({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  const state = parseState((await searchParams).state);
  const { data: p, source, reason, endpoint } = await loadSkillProfile(state);

  if (p.skills.length === 0) {
    return (
      <>
        <PageHeader
          eyebrow="Gap map"
          title="Every skill, and the evidence behind it"
          actions={
            <IosButton href="/onboarding" variant="primary" size="md" arrow>
              Upload resume and JD
            </IosButton>
          }
        />
        <section className="card-surface p-8 lg:p-12 text-center">
          <span
            aria-hidden
            className="inline-flex items-center justify-center size-11 rounded-full bg-[var(--brand-soft)] text-[var(--brand-strong)] mb-4"
          >
            <ScanSearch size={20} />
          </span>
          <h2 className="type-display-3 m-0 mb-3">No skills scored yet</h2>
          <p className="type-body text-[var(--text-dim)] m-0 max-w-[52ch] mx-auto">
            The gap map is built from real requirements in your job description
            and real claims in your resume. Nothing here is pre-filled — an empty
            map means the analysis has not run, not that you have no gaps.
          </p>
        </section>
        <div className="mt-6 flex flex-wrap items-center gap-2">
          <DataSourceBadge source={source} endpoint={endpoint} reason={reason} />
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader
        eyebrow={`${p.skills.length} skills · ${p.counts.verified} verified`}
        title="Every skill, and the evidence behind it"
        actions={
          <IosButton href="/roadmap" variant="primary" size="md" arrow>
            Open roadmap
          </IosButton>
        }
      />

      {p.provisional && (
        <div className="mb-5">
          <StateNotice title="This map is provisional">
            {p.counts.critical} critical and {p.counts.high} high-band skills
            still need assessment evidence. Bands are recomputed on every answer,
            so nothing here is frozen.
          </StateNotice>
        </div>
      )}

      <div className="space-y-5">
        <SkillMatrix
          skills={p.skills}
          asOf={source === "database" ? new Date().toISOString() : undefined}
        />
        <GapMapTable skills={p.skills} />
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3 type-small text-[var(--text-dim)]">
        <span>
          Priority = JD importance × gap × interview relevance. Bands: ≥0.55
          critical, ≥0.35 high, ≥0.18 medium, else low.
        </span>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 font-medium text-[var(--brand-strong)] hover:underline underline-offset-4"
        >
          Back to dashboard
          <ArrowRight size={14} aria-hidden />
        </Link>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <DataSourceBadge source={source} endpoint={endpoint} reason={reason} />
      </div>
    </>
  );
}

function GapMapLoading() {
  return (
    <div className="space-y-5" aria-busy="true" aria-live="polite">
      <span className="sr-only">Loading your gap map</span>
      <Skeleton className="h-8 w-72" />
      <div className="card-surface p-5 space-y-3">
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} className="h-8" />
        ))}
      </div>
      <div className="card-surface p-5 space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12" />
        ))}
      </div>
    </div>
  );
}
