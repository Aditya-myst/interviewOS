import { Suspense } from "react";
import Link from "next/link";
import AssessmentLadder from "@/components/app/AssessmentLadder";
import DataSourceBadge from "@/components/app/DataSourceBadge";
import Skeleton from "@/components/app/Skeleton";
import PriorityScatter from "@/components/charts/PriorityScatter";
import { loadSkillProfile } from "@/lib/api";
import { parseState } from "@/lib/fixtures";

export const metadata = { title: "Assessment ladder — InterviewOS" };

/**
 * The ladder screen, for one skill.
 *
 * `?skill=<id>` picks the skill; without it the page lists what can be assessed, in
 * priority order, so the screen is never a dead end. Every skill here comes from the
 * candidate's own profile — a marketing candidate sees content and SEO, not FastAPI.
 */
export default async function AssessmentPage({
  searchParams,
}: {
  searchParams: Promise<{ state?: string; skill?: string }>;
}) {
  return (
    <Suspense fallback={<Skeleton className="h-[340px] w-full" />}>
      <AssessmentBody searchParams={searchParams} />
    </Suspense>
  );
}

async function AssessmentBody({
  searchParams,
}: {
  searchParams: Promise<{ state?: string; skill?: string }>;
}) {
  const { state, skill: wanted } = await searchParams;
  const demo = parseState(state);
  const profile = await loadSkillProfile(demo);
  const skills = [...(profile.data.skills ?? [])].sort(
    (a, b) => (b.priority ?? 0) - (a.priority ?? 0),
  );
  const chosen = wanted ? skills.find((row) => row.skill_id === wanted) : undefined;

  return (
    <div className="grid gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="type-micro m-0 text-[var(--text-dim)]">Assessment</p>
          <h1 className="mt-1 mb-0 text-[30px] font-semibold leading-tight tracking-[-0.02em]">
            Three questions instead of a guess
          </h1>
          <p className="mt-1 type-small m-0 text-[var(--text-dim)]">
            A short ladder per skill: concept, mechanics, then the work itself. Scored on the
            rubric for one curriculum subtopic, with the quote that earned it.
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
          <h2 className="text-[20px] font-semibold">Nothing to assess yet</h2>
          <p className="mt-2 type-small text-[var(--text-dim)]">
            The ladder probes the skills your resume and the job description produced. Upload
            both first.
          </p>
        </section>
      ) : chosen ? (
        <>
          <AssessmentLadder
            skillId={chosen.skill_id}
            skillName={chosen.name}
            band={chosen.priority_band}
            status={chosen.status}
          />
          <section className="card-surface p-5">
            <h2 className="m-0 text-[15px] font-semibold">Why this skill is on your list</h2>
            <p className="type-small mt-2 mb-0 text-[var(--text-dim)]">{chosen.explanation}</p>
            <p className="type-micro mt-3 mb-0 text-[var(--text-dim)]">
              priority {chosen.priority?.toFixed(2)} · gap {chosen.gap?.toFixed(2)} ·{" "}
              {chosen.in_jd ? "asked for in the JD" : "not in the JD"} ·{" "}
              {chosen.in_resume ? "on your resume" : "not on your resume"}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Link
                href={`/assessment?state=${demo}${skills
                  .filter((row) => row.skill_id !== chosen.skill_id)
                  .slice(0, 1)
                  .map((row) => `&skill=${row.skill_id}`)
                  .join("")}`}
                className="type-small rounded-full border border-[var(--border-strong)] px-3 py-1.5 text-[var(--text-dim)]"
              >
                Next skill in priority order →
              </Link>
              <Link
                href="/gap-map"
                className="type-small rounded-full border border-[var(--border-strong)] px-3 py-1.5 text-[var(--text-dim)]"
              >
                Back to the gap map
              </Link>
            </div>
          </section>
        </>
      ) : (
        <>
          <section className="card-surface p-5">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="m-0 text-[15px] font-semibold">Pick a skill</h2>
              <span className="type-micro text-[var(--text-dim)]">
                highest priority first · {skills.length} skills
              </span>
            </div>
            <ul className="mt-3 grid list-none gap-1 p-0">
              {skills.slice(0, 8).map((row) => (
                <li key={row.skill_id}>
                  <Link
                    href={`/assessment?state=${demo}&skill=${row.skill_id}`}
                    className="flex items-center gap-3 rounded-[10px] px-2 py-2 no-underline hover:bg-[var(--surface-2)]"
                  >
                    <span className="type-small font-medium text-[var(--text)]">{row.name}</span>
                    <span className="type-micro text-[var(--text-dim)]">{row.priority_band}</span>
                    <span className="ml-auto font-mono text-[12px] tabular-nums text-[var(--text-dim)]">
                      {row.priority?.toFixed(2)}
                    </span>
                    <span className="type-micro capitalize text-[var(--text-dim)]">
                      {row.status.replace("_", " ")}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
          <section className="card-surface p-5">
            <h2 className="m-0 text-[15px] font-semibold">Where the gaps sit</h2>
            <PriorityScatter skills={profile.data.skills} />
          </section>
        </>
      )}
    </div>
  );
}
