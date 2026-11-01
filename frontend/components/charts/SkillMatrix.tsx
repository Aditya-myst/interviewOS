import type { CandidateSkill } from "../../../contracts/types";
import { FIXTURE_TODAY } from "@/lib/fixtures";

/**
 * Nine rows, three tinted columns: how much the job cares, how much evidence
 * exists, how recent it is. Replaces a paragraph per row with a shape per row.
 * Cells link to the detailed row further down the page.
 */
function daysSince(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = Math.round((Date.parse(FIXTURE_TODAY) - Date.parse(iso)) / 86_400_000);
  if (d <= 0) return "today";
  if (d === 1) return "1d";
  return `${d}d`;
}

export default function SkillMatrix({ skills }: { skills: CandidateSkill[] }) {
  const rows = [...skills].sort((a, b) => b.priority - a.priority);

  return (
    <div className="card-surface overflow-hidden">
      <div className="flex items-center justify-between gap-4 px-4 py-3 border-b border-[var(--border)]">
        <h2 className="type-h4 m-0">Skill matrix</h2>
        <span className="type-micro text-[var(--text-dim)]">
          importance · evidence · recency
        </span>
      </div>

      <ul className="list-none m-0 p-0">
        {rows.map((s) => {
          const evidenceCells = Math.min(s.evidence.length, 2);
          return (
            <li key={s.skill_id} className="border-b border-[var(--border)] last:border-0">
              <a
                href={`#skill-${s.skill_id}`}
                className="flex items-center gap-3 px-4 py-2.5 hover:bg-[var(--surface)] transition-colors"
              >
                <span className="w-[38%] min-w-0 truncate type-small font-medium text-[var(--text)]">
                  {s.name}
                </span>

                {/* JD importance */}
                <span className="flex-1 min-w-0">
                  <span className="block h-2 rounded-[999px] bg-[var(--surface-3)] overflow-hidden">
                    <span
                      className="block h-full bg-[var(--brand-strong)]"
                      style={{ width: `${Math.round(s.jd_importance * 100)}%` }}
                    />
                  </span>
                </span>

                {/* evidence: 0 / 1 / 2+ quotes */}
                <span className="flex items-center gap-1 shrink-0" aria-hidden>
                  {[0, 1].map((i) => (
                    <span
                      key={i}
                      className={`size-2.5 rounded-[2px] ${
                        i < evidenceCells
                          ? "bg-[var(--brand)]"
                          : "bg-[var(--surface-3)]"
                      }`}
                    />
                  ))}
                </span>

                <span className="w-[52px] text-right type-small text-[var(--text-dim)] tabular-nums shrink-0">
                  {daysSince(s.last_assessed_at)}
                </span>

                <span
                  className={`w-[74px] shrink-0 text-right type-micro ${
                    s.status === "verified"
                      ? "text-[var(--verified)]"
                      : s.status === "weak"
                        ? "text-[var(--weak)]"
                        : s.status === "developing"
                          ? "text-[var(--developing)]"
                          : "text-[var(--text-dim)]"
                  }`}
                >
                  {s.status.replace("_", " ")}
                </span>
              </a>
            </li>
          );
        })}
      </ul>

      <p className="px-4 py-2.5 m-0 type-small text-[var(--text-dim)] border-t border-[var(--border)]">
        Filled squares are evidence quotes on file. Click a row for the quotes.
      </p>
    </div>
  );
}
