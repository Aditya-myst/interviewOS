import { Suspense } from "react";
import InterviewRoom from "@/components/app/InterviewRoom";
import Skeleton from "@/components/app/Skeleton";
import DataSourceBadge from "@/components/app/DataSourceBadge";
import { loadDashboard, loadSkillProfile } from "@/lib/api";
import { parseState } from "@/lib/fixtures";

export const metadata = { title: "Mock interview — InterviewOS" };

/**
 * The interview screen.
 *
 * It asks the profile for the same priority order the dashboard shows, so the practice
 * session and the plan agree with each other. Nothing about this page is role-specific:
 * the questions come from whatever skills the candidate's own JD produced.
 */
export default async function InterviewPage({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  return (
    <Suspense fallback={<Skeleton className="h-[340px] w-full" />}>
      <InterviewBody searchParams={searchParams} />
    </Suspense>
  );
}

async function InterviewBody({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  const { state } = await searchParams;
  const demo = parseState(state);
  const [profile, dashboard] = await Promise.all([loadSkillProfile(demo), loadDashboard(demo)]);
  // The target role comes from the profile the candidate set, not from the first skill's
  // category — "AI" is not a role anyone applies for.
  const role = dashboard.data.target_role ?? "your target role";
  const skills = profile.data.skills ?? [];

  // Priority order is the engine's own: highest priority first, as the curve shows.
  const ranked = [...skills]
    .sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0))
    .slice(0, 6)
    .map((skill) => ({ skill: skill.name, band: skill.priority_band }));

  return (
    <div className="grid gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="type-micro text-[var(--text-dim)] m-0">Interview</p>
          <h1 className="mt-1 mb-0 text-[30px] font-semibold leading-tight tracking-[-0.02em]">
            Practise the questions this role will ask
          </h1>
          <p className="mt-1 type-small text-[var(--text-dim)] m-0">
            Scored against a rubric, with a quote for every point you earn.
          </p>
        </div>
        <DataSourceBadge
          source={profile.source}
          reason={profile.reason}
          endpoint={profile.endpoint}
        />
      </header>

      {skills.length === 0 ? (
        <section className="card-surface p-8 text-center">
          <h2 className="text-[20px] font-semibold">No scored skills yet</h2>
          <p className="mt-2 type-small text-[var(--text-dim)]">
            Upload a resume and paste a job description first — the interview asks about the
            gaps that produces, and it refuses to invent questions.
          </p>
        </section>
      ) : (
        <InterviewRoom
          role={role}
          coverage={ranked}
          skills={skills.length}
          questionCount={Math.min(5, Math.max(3, ranked.length))}
        />
      )}
    </div>
  );
}
