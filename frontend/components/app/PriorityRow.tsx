import { ArrowRight } from "lucide-react";
import type { CandidateSkill } from "../../../contracts/types";
import SkillPill from "@/components/primitives/SkillPill";

const BAND: Record<string, { label: string; className: string }> = {
  critical: { label: "CRITICAL", className: "bg-[var(--weak)]/12 text-[var(--weak)]" },
  high: { label: "HIGH", className: "bg-[var(--developing)]/12 text-[var(--developing)]" },
  medium: { label: "MEDIUM", className: "bg-[var(--brand)]/12 text-[var(--brand-strong)]" },
  low: { label: "LOW", className: "bg-[var(--surface-2)] text-[var(--text-dim)]" },
};

/**
 * One priority skill. `explanation` is rendered verbatim — the server wrote the
 * sentence and the UI is not allowed to reword it, which is the whole claim.
 */
export default function PriorityRow({ skill }: { skill: CandidateSkill }) {
  const band = BAND[skill.priority_band] ?? BAND.low;

  return (
    <article className="group p-5 border-b border-[var(--border)] last:border-b-0 hover:bg-[var(--surface)]/60 transition-colors">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="min-w-0">
          <h3 className="type-h4 text-[var(--text)] m-0 truncate">{skill.name}</h3>
          <p className="m-0 mt-1 type-small text-[var(--text-dim)]">
            {skill.category ?? "Uncategorised"}
            {skill.expected_level ? ` · expected ${skill.expected_level}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <SkillPill label={skill.status.replace("_", " ")} status={skill.status} />
          <span
            className={`px-2 py-1 rounded-[999px] text-[11px] font-semibold tracking-[0.06em] ${band.className}`}
          >
            {band.label}
          </span>
        </div>
      </div>

      <p className="type-small text-[var(--text-dim)] m-0 mb-3 max-w-[62ch]">
        {skill.explanation}
      </p>

      <div className="flex items-center gap-4">
        <span className="font-mono text-[11px] text-[var(--text-dim)] tabular-nums">
          priority {skill.priority.toFixed(2)}
        </span>
        <span className="font-mono text-[11px] text-[var(--text-dim)] tabular-nums">
          gap {skill.gap.toFixed(2)}
        </span>
        <span className="font-mono text-[11px] text-[var(--text-dim)] tabular-nums">
          evidence {skill.evidence.length}
        </span>
        <a
          href="/gap-map"
          className="ml-auto inline-flex items-center gap-1.5 type-small font-medium text-[var(--brand-strong)] hover:underline underline-offset-4"
        >
          {skill.status === "unverified" ? "Assess this first" : "Review evidence"}
          <ArrowRight size={14} aria-hidden />
        </a>
      </div>
    </article>
  );
}
