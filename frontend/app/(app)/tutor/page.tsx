import { Suspense } from "react";
import Link from "next/link";
import DataSourceBadge from "@/components/app/DataSourceBadge";
import Skeleton from "@/components/app/Skeleton";
import TutorChat from "@/components/app/TutorChat";
import { loadSkillProfile } from "@/lib/api";
import { parseState } from "@/lib/fixtures";

export const metadata = { title: "Tutor — InterviewOS" };

/**
 * The tutor screen.
 *
 * The starter questions come from the candidate's own profile, in priority order — a
 * marketing candidate is offered content and analytics, not FastAPI. The chat itself is a
 * client component because the answer is a POST; everything above it is server-rendered so
 * the page still says who it is talking about before a single request is made.
 */
export default async function TutorPage({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  return (
    <Suspense fallback={<Skeleton className="h-[420px] w-full" />}>
      <TutorBody searchParams={searchParams} />
    </Suspense>
  );
}

async function TutorBody({ searchParams }: { searchParams: Promise<{ state?: string }> }) {
  const { state } = await searchParams;
  const demo = parseState(state);
  const profile = await loadSkillProfile(demo);
  const skills = [...(profile.data.skills ?? [])].sort(
    (a, b) => (b.priority ?? 0) - (a.priority ?? 0),
  );
  const suggestions = skills.slice(0, 3).map((row) => `How do I close the gap in ${row.name}?`);

  return (
    <div className="grid gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="type-micro m-0 text-[var(--text-dim)]">Tutor</p>
          <h1 className="mt-1 mb-0 text-[30px] font-semibold leading-tight tracking-[-0.02em]">
            Every answer cites the row it came from
          </h1>
          <p className="mt-1 max-w-[62ch] type-small m-0 text-[var(--text-dim)]">
            Scoped to your own gaps. It explains the next three subtopics from the curriculum and
            links the curated resources for them — and when there is no row, it says so instead of
            improvising.
          </p>
        </div>
        <DataSourceBadge
          source={profile.source}
          reason={profile.reason}
          endpoint={profile.endpoint}
        />
      </header>

      <TutorChat suggestions={suggestions} demoState={state} />

      {skills.length > 0 && (
        <section className="rounded-[16px] border border-[var(--border)] bg-[var(--surface)] p-5">
          <div className="flex items-baseline justify-between gap-3">
            <h2 className="m-0 text-[15px] font-semibold text-[var(--text)]">On your list</h2>
            <Link href="/gap-map" className="type-micro text-[var(--text-dim)] hover:text-[var(--text)]">
              Full gap map →
            </Link>
          </div>
          <ul className="m-0 mt-3 grid list-none gap-2 p-0 sm:grid-cols-2">
            {skills.slice(0, 6).map((row) => (
              <li
                key={row.skill_id}
                className="flex items-center justify-between gap-2 rounded-[10px] border border-[var(--border)] px-3 py-2"
              >
                <span className="truncate type-small text-[var(--text)]">{row.name}</span>
                <span className="shrink-0 type-micro text-[var(--text-dim)]">
                  {row.priority_band} · gap {Math.round((row.gap ?? 0) * 100)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
