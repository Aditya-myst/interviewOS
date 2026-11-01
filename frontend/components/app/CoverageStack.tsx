import type { CoverageRow } from "../../../contracts/types";

/**
 * Coverage as stacked bars: counts of skills, not percentages dressed up as
 * evidence. Contract CoverageRow only carries three buckets, so the mapping is
 * explicit — verified stays verified, developing stays developing, and
 * claimed / unverified / weak all count as "unverified" here because none of
 * them is proven. Weak is not hidden; the band it lives in is.
 */
export default function CoverageStack({ rows }: { rows: CoverageRow[] }) {
  const total = rows.reduce(
    (n, r) => n + r.verified + r.developing + r.unverified,
    0
  );

  return (
    <ul className="list-none m-0 p-0 space-y-3.5">
      {rows.map((r) => {
        const rowTotal = r.verified + r.developing + r.unverified || 1;
        const seg = (n: number) => `${(n / rowTotal) * 100}%`;
        return (
          <li key={r.category}>
            <div className="flex items-baseline justify-between mb-1.5">
              <span className="type-small font-medium text-[var(--text)]">
                {r.category}
              </span>
              <span className="type-small text-[var(--text-dim)] tabular-nums">
                {r.verified}/{rowTotal} verified
              </span>
            </div>
            <div
              className="flex h-2 rounded-[999px] overflow-hidden bg-[var(--surface-3)]"
              role="img"
              aria-label={`${r.category}: ${r.verified} verified, ${r.developing} developing, ${r.unverified} unverified`}
            >
              {r.verified > 0 && (
                <span style={{ width: seg(r.verified) }} className="bg-[var(--brand)]" />
              )}
              {r.developing > 0 && (
                <span
                  style={{ width: seg(r.developing) }}
                  className="bg-[var(--developing)]"
                />
              )}
              {r.unverified > 0 && (
                <span
                  style={{ width: seg(r.unverified) }}
                  className="bg-[var(--unverified)]/45"
                />
              )}
            </div>
          </li>
        );
      })}
      <li className="flex flex-wrap items-center gap-x-4 gap-y-1.5 pt-2 text-xs text-[var(--text-dim)]">
        {[
          ["Verified", "var(--brand)"],
          ["Developing", "var(--developing)"],
          ["Unverified", "var(--unverified)"],
        ].map(([label, color]) => (
          <span key={label} className="inline-flex items-center gap-1.5">
            <span
              className="size-2 rounded-full"
              style={{ background: color }}
              aria-hidden
            />
            {label}
          </span>
        ))}
        <span className="ml-auto tabular-nums">{total} skills tracked</span>
      </li>
    </ul>
  );
}
