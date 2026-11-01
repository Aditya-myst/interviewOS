import { CheckCircle2, Clock, ExternalLink } from "lucide-react";
import PageHeader from "@/components/shell/PageHeader";
import IosButton from "@/components/primitives/IosButton";
import { roadmapFixture } from "@/lib/fixtures";
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

export default function RoadmapPage() {
  const r = roadmapFixture;
  const done = r.progress?.done ?? 0;
  const total = r.progress?.total ?? r.topics.length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="max-w-[1180px] mx-auto">
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

      <ol className="list-none m-0 p-0 space-y-4">
        {r.topics.map((t) => (
          <li key={t.id}>
            <TopicCard topic={t} />
          </li>
        ))}
      </ol>

      <p className="mt-6 type-small text-[var(--text-dim)]">
        Every resource below was resolved against the curated catalogue and
        HTTP-checked before it was shown — no generated links. Fixture data:
        contracts/fixtures/roadmap.json.
      </p>
    </div>
  );
}

function TopicCard({ topic }: { topic: LearningTopic }) {
  const progressPct = Math.round(topic.progress * 100);
  const grouped = (["concept", "practice", "checkpoint"] as const).map((role) => ({
    role,
    items: topic.resources.filter((res) => res.role === role),
  }));

  return (
    <article className="card-surface p-5 lg:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[11px] text-[var(--text-dim)] tabular-nums">
            {String(topic.order_index + 1).padStart(2, "0")}
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

      <ul className="list-none m-0 p-0 mb-4 flex flex-wrap gap-1.5">
        {(topic.subtopics ?? []).map((s) => (
          <li
            key={s}
            className="type-small px-2.5 py-1 rounded-[999px] bg-[var(--surface-2)] text-[var(--text-dim)]"
          >
            {s}
          </li>
        ))}
      </ul>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {grouped.map(({ role, items }) => (
          <div key={role} className="rounded-[12px] border border-[var(--border)] p-3">
            <p className="type-micro text-[var(--text-dim)] m-0 mb-2">
              {ROLE_LABEL[role]}
            </p>
            {items.length === 0 ? (
              <p className="type-small text-[var(--text-dim)] m-0">
                Not resolved yet — shows a labelled search, never a fake link.
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
      {res.verified_at && (
        <p className="m-0 mt-1.5 inline-flex items-center gap-1 type-micro text-[var(--verified)]">
          <CheckCircle2 size={11} aria-hidden />
          link checked
        </p>
      )}
    </div>
  );
}
