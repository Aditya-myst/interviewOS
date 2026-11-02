import { Suspense } from "react";
import { CheckCircle2, Clock, CircleDashed, ExternalLink, TriangleAlert } from "lucide-react";
import PageHeader from "@/components/shell/PageHeader";
import IosButton from "@/components/primitives/IosButton";
import DataSourceBadge from "@/components/app/DataSourceBadge";
import StateNotice from "@/components/app/StateNotice";
import Skeleton from "@/components/app/Skeleton";
import { loadRoadmap } from "@/lib/api";
import { parseState } from "@/lib/fixtures";
import type { LearningTopic, Resource } from "../../../../contracts/types";

export const metadata = { title: "Roadmap — InterviewOS" };

const STATUS_STYLE: Record<string, string> = {
  done: "bg-[var(--brand)] text-[var(--ink-950)]",
  checkpoint_passed: "bg-[var(--brand-soft)] text-[var(--brand-strong)]",
  in_progress: "bg-[var(--developing)]/15 text-[var(--developing)]",
  not_started: "bg-[var(--surface-2)] text-[var(--text-dim)]",
};

const STATUS_LABEL: Record<string, string> = {
  done: "Done",
  checkpoint_passed: "Checkpoint passed",
  in_progress: "In progress",
  not_started: "Not started",
};

const DEPTH_LABEL: Record<string, string> = {
  refresh: "Refresh",
  core: "Core",
  deep_dive: "Deep dive",
};

const ROLE_LABEL: Record<string, string> = {
  concept: "Learn the concept",
  practice: "Practise it",
  checkpoint: "Prove it",
};

/**
 * The roadmap reads `/v1/learning/roadmap`. Topics are subtopics from the
 * curriculum graph, never invented, and a slot the catalogue cannot fill is
 * reported as a named gap (`missing_roles`) rather than an empty box that looks
 * finished. That is the whole reason this page exists in this shape.
 */
export default function RoadmapPage({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  return (
    <div className="max-w-[1180px] mx-auto">
      <Suspense fallback={<RoadmapLoading />}>
        <RoadmapBody searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function RoadmapBody({
  searchParams,
}: {
  searchParams: Promise<{ state?: string }>;
}) {
  const state = parseState((await searchParams).state);
  const { data: r, source, reason, endpoint } = await loadRoadmap(state);

  const done = r.progress?.done ?? 0;
  const total = r.progress?.total ?? r.topics.length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  const gaps = r.topics.reduce((n, t) => n + (t.missing_roles?.length ?? 0), 0);

  return (
    <>
      <PageHeader
        eyebrow={`Roadmap · ${r.target_role ?? "target role"}`}
        title="What to study, in order"
        actions={
          <IosButton href="/gap-map" variant="secondary" size="md">
            Review gaps
          </IosButton>
        }
      />

      <section className="slab-ink p-6 mb-6">
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div className="max-w-[62ch]">
            <p className="type-micro text-[var(--on-ink-dim)] m-0 mb-2">
              Why this order
            </p>
            <p className="type-body text-[var(--on-ink)] m-0">{r.summary}</p>
          </div>
          <div className="shrink-0">
            <p className="type-micro text-[var(--on-ink-dim)] m-0 mb-2">
              Progress
            </p>
            <p className="font-mono tabular-nums text-[28px] leading-none text-[var(--on-ink)] m-0">
              {done}/{total}
              <span className="text-[14px] text-[var(--on-ink-dim)] ml-2">
                topics · {pct}%
              </span>
            </p>
          </div>
        </div>
      </section>

      {gaps > 0 && (
        <div className="mb-5">
          <StateNotice kind="warn" title={`${gaps} resource slot${gaps === 1 ? "" : "s"} the catalogue cannot fill`}>
            Each topic below names the roles it is missing — usually a checkpoint,
            because a checkpoint has to be something you can fail and a blog post
            is not. Nothing is substituted with a generated link to make the page
            look complete.
          </StateNotice>
        </div>
      )}

      {r.topics.length === 0 ? (
        <section className="card-surface p-8 lg:p-12 text-center">
          <h2 className="type-display-3 m-0 mb-3">No plan yet</h2>
          <p className="type-body text-[var(--text-dim)] m-0 max-w-[52ch] mx-auto">
            A roadmap needs scored skills first. Run the JD analysis and the
            first plan appears here, ordered by priority.
          </p>
        </section>
      ) : (
        <ol className="list-none m-0 p-0 space-y-4">
          {r.topics.map((t) => (
            <li key={t.id}>
              <TopicCard topic={t} />
            </li>
          ))}
        </ol>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-2">
        <DataSourceBadge source={source} endpoint={endpoint} reason={reason} />
        <span className="type-small text-[var(--text-dim)]">
          Topics come from the curriculum graph in data/taxonomy.yaml; resources
          come from the 75-link catalogue in data/curated.yaml, each HTTP-checked.
        </span>
      </div>
    </>
  );
}

function TopicCard({ topic }: { topic: LearningTopic }) {
  const progressPct = Math.round((topic.progress ?? 0) * 100);
  const missing = topic.missing_roles ?? [];
  const grouped = (["concept", "practice", "checkpoint"] as const).map((role) => ({
    role,
    items: (topic.resources ?? []).filter((res) => res.role === role),
    missing: missing.includes(role),
  }));

  return (
    <article className="card-surface p-5 lg:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-[var(--text-dim)] tabular-nums">
            {String((topic.order_index ?? 0) + 1).padStart(2, "0")}
          </span>
          <h2 className="type-h4 m-0">{topic.title}</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="type-micro text-[var(--text-dim)] px-2 py-1 rounded-[999px] border border-[var(--border)]">
            {DEPTH_LABEL[topic.depth] ?? topic.depth}
          </span>
          <span
            className={`type-micro px-2 py-1 rounded-[999px] ${
              STATUS_STYLE[topic.status] ?? STATUS_STYLE.not_started
            }`}
          >
            {STATUS_LABEL[topic.status] ?? topic.status}
          </span>
        </div>
      </div>

      <p className="type-small text-[var(--text-dim)] m-0 mb-3 max-w-[72ch]">
        {topic.skill_name ? `${topic.skill_name} · ` : ""}
        {topic.objective}
      </p>

      <div className="flex items-center gap-3 mb-4">
        <div className="flex-1 h-1.5 rounded-[999px] bg-[var(--surface-3)] overflow-hidden">
          <div
            className="h-full bg-[var(--brand)]"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <span className="type-small text-[var(--text-dim)] tabular-nums shrink-0 inline-flex items-center gap-1">
          <Clock size={13} aria-hidden />
          {topic.estimated_minutes ? `${topic.estimated_minutes} min` : "—"}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {grouped.map(({ role, items, missing: isMissing }) => (
          <div
            key={role}
            className={`rounded-[12px] border p-3 ${
              isMissing
                ? "border-dashed border-[var(--developing)]/45 bg-[var(--developing)]/[0.06]"
                : "border-[var(--border)]"
            }`}
          >
            <p className="type-micro text-[var(--text-dim)] m-0 mb-2 flex items-center gap-1.5">
              {ROLE_LABEL[role]}
              {isMissing && (
                <span className="inline-flex items-center gap-1 text-[var(--developing)]">
                  <TriangleAlert size={11} aria-hidden />
                  gap
                </span>
              )}
            </p>
            {items.length === 0 ? (
              <p className="type-small text-[var(--developing)] m-0">
                Not in the catalogue yet. Shown as a named gap, never a generated
                link.
              </p>
            ) : (
              <ul className="list-none m-0 p-0 space-y-3">
                {items.map((res) => (
                  <li key={res.id}>
                    <ResourceLink res={res} />
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </article>
  );
}

function ResourceLink({ res }: { res: Resource }) {
  return (
    <div>
      <a
        href={res.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-start gap-1.5 type-small font-medium text-[var(--text)] hover:text-[var(--brand-strong)] hover:underline underline-offset-4"
      >
        <span>{res.title}</span>
        <ExternalLink size={13} className="mt-0.5 shrink-0" aria-hidden />
      </a>
      <p className="m-0 mt-1 type-micro text-[var(--text-dim)]">
        {res.provider}
        {res.duration_minutes ? ` · ${res.duration_minutes} min` : ""}
        {res.is_paid ? " · paid" : " · free"}
      </p>
      {res.why && (
        <p className="m-0 mt-1.5 type-small text-[var(--text-dim)]">{res.why}</p>
      )}
      {res.verified_at ? (
        <p className="m-0 mt-1.5 inline-flex items-center gap-1 type-micro text-[var(--verified)]">
          <CheckCircle2 size={11} aria-hidden />
          link checked
        </p>
      ) : (
        <p className="m-0 mt-1.5 inline-flex items-center gap-1 type-micro text-[var(--text-dim)]">
          <CircleDashed size={11} aria-hidden />
          not machine-checked
        </p>
      )}
    </div>
  );
}

function RoadmapLoading() {
  return (
    <div className="space-y-4" aria-busy="true" aria-live="polite">
      <span className="sr-only">Loading your roadmap</span>
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-28" />
      {Array.from({ length: 3 }).map((_, i) => (
        <Skeleton key={i} className="h-52" />
      ))}
    </div>
  );
}
