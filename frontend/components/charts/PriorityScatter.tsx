import type { CandidateSkill } from "../../../contracts/types";

/**
 * The money chart: importance against gap, bubble size by interview relevance.
 * Top-right is "the interview will ask this and you cannot prove it yet" — the
 * order of the list is legible from the shape, which is the whole point.
 *
 * Static SVG on purpose: native <title> gives hover text without shipping JS,
 * and the sr-only table below is the accessible equivalent.
 */
const BAND_COLOR: Record<string, string> = {
  critical: "var(--weak)",
  high: "var(--developing)",
  medium: "var(--brand-strong)",
  low: "var(--unverified)",
};

const W = 440;
const H = 280;
const PAD = 34;

export default function PriorityScatter({ skills }: { skills: CandidateSkill[] }) {
  const x = (gap: number) => PAD + gap * (W - PAD * 2);
  const y = (imp: number) => H - PAD - imp * (H - PAD * 2);

  // Top three get a numbered badge instead of a text label: three names in the
  // same corner of one chart overlap, and a legend reads faster than leaders.
  const top = [...skills].sort((a, b) => b.priority - a.priority).slice(0, 3);
  const rank = new Map(top.map((s, i) => [s.skill_id, i + 1]));

  return (
    <figure className="m-0">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full h-auto"
        role="img"
        aria-label="Skills plotted by job-description importance and evidence gap"
      >
        {/* grid */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => (
          <g key={t}>
            <line
              x1={x(t)}
              y1={y(0)}
              x2={x(t)}
              y2={y(1)}
              stroke="var(--border)"
              strokeWidth={1}
            />
            <line
              x1={x(0)}
              y1={y(t)}
              x2={x(1)}
              y2={y(t)}
              stroke="var(--border)"
              strokeWidth={1}
            />
          </g>
        ))}

        {/* fix-first quadrant */}
        <rect
          x={x(0.5)}
          y={y(1)}
          width={x(1) - x(0.5)}
          height={y(0.5) - y(1)}
          fill="var(--weak)"
          opacity={0.05}
        />
        <text
          x={W - PAD}
          y={15}
          textAnchor="end"
          className="fill-[var(--weak)]"
          style={{ fontSize: 9, letterSpacing: "0.08em" }}
        >
          FIX FIRST ↗
        </text>

        {/* points */}
        {skills.map((s) => {
          const cx = x(Math.min(Math.max(s.gap, 0), 1));
          const cy = y(Math.min(Math.max(s.jd_importance, 0), 1));
          const r = 5 + s.interview_relevance * 7;
          const n = rank.get(s.skill_id);
          return (
            <g key={s.skill_id}>
              <circle
                cx={cx}
                cy={cy}
                r={r}
                fill={BAND_COLOR[s.priority_band] ?? BAND_COLOR.low}
                opacity={0.85}
              >
                <title>{`${s.name} — ${s.priority_band}, priority ${s.priority.toFixed(2)}`}</title>
              </circle>
              {n && (
                <text
                  x={cx}
                  y={cy + 3.5}
                  textAnchor="middle"
                  style={{ fontSize: 10, fontWeight: 700 }}
                  className="fill-white"
                >
                  {n}
                </text>
              )}
            </g>
          );
        })}

        {/* axes */}
        <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(0)} stroke="var(--border-strong)" />
        <line x1={x(0)} y1={y(0)} x2={x(0)} y2={y(1)} stroke="var(--border-strong)" />
        <text
          x={x(0.5)}
          y={H - 8}
          textAnchor="middle"
          style={{ fontSize: 9.5, letterSpacing: "0.06em" }}
          className="fill-[var(--text-dim)]"
        >
          EVIDENCE GAP →
        </text>
        <text
          x={12}
          y={y(0.5)}
          textAnchor="middle"
          transform={`rotate(-90 12 ${y(0.5)})`}
          style={{ fontSize: 9.5, letterSpacing: "0.06em" }}
          className="fill-[var(--text-dim)]"
        >
          JD IMPORTANCE →
        </text>
      </svg>

      {/* numbered list = the labels the chart cannot carry without overlap */}
      <ol className="mt-2 mb-2 list-none p-0 space-y-1">
        {top.map((s, i) => (
          <li key={s.skill_id} className="flex items-baseline gap-2 type-small">
            <span className="font-mono text-[11px] text-[var(--text-dim)] tabular-nums">
              {i + 1}
            </span>
            <span className="text-[var(--text)]">{s.name}</span>
            <span className="ml-auto text-[var(--text-dim)] tabular-nums text-xs">
              {s.priority_band} · {s.priority.toFixed(2)}
            </span>
          </li>
        ))}
      </ol>

      <figcaption className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-[var(--text-dim)]">
        {[
          ["Critical", "var(--weak)"],
          ["High", "var(--developing)"],
          ["Medium", "var(--brand-strong)"],
          ["Low", "var(--unverified)"],
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
        <span className="ml-auto">bubble size = interview relevance</span>
      </figcaption>

      <table className="sr-only">
        <caption>Priorities by importance and gap</caption>
        <thead>
          <tr>
            <th scope="col">Skill</th>
            <th scope="col">JD importance</th>
            <th scope="col">Gap</th>
            <th scope="col">Priority</th>
            <th scope="col">Band</th>
          </tr>
        </thead>
        <tbody>
          {skills.map((s) => (
            <tr key={s.skill_id}>
              <td>{s.name}</td>
              <td>{s.jd_importance}</td>
              <td>{s.gap}</td>
              <td>{s.priority}</td>
              <td>{s.priority_band}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
