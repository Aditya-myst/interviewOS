import type { CandidateSkill } from "../../../contracts/types";

/**
 * Priority, as a curve rather than a cloud.
 *
 * The scatter this replaces was technically faithful — importance on one axis, gap
 * on the other — and unreadable: nine dots in a small square, four of them
 * overlapping, and no sense of *order*. The question a candidate actually asks is
 * "what first, and how much further ahead is it", and that is a line.
 *
 * So: skills sorted by priority, one node each, joined so the drop from the first
 * to the tenth is visible at a glance. Node colour is the band (same thresholds as
 * the gap map), node size is interview relevance, the number above the top three is
 * the order to work in, and the dashed rule is the critical band's lower edge.
 */
const BAND_COLOR: Record<string, string> = {
  critical: "#dc2626",
  high: "#b45309",
  medium: "#6b7a72",
  low: "#9aa8a0",
};

const LABEL_MAX = 20;

function shorten(name: string): string {
  return name.length > LABEL_MAX ? `${name.slice(0, LABEL_MAX - 1)}…` : name;
}

export default function PriorityCurve({ skills }: { skills: CandidateSkill[] }) {
  // Six, not ten: rotated labels need ~90px each to stay readable, and this chart's
  // job is to answer "what first", not to be the complete table.
  const ranked = [...skills].sort((a, b) => b.priority - a.priority).slice(0, 6);

  if (ranked.length === 0) {
    return (
      <div className="flex h-[232px] items-center justify-center">
        <p className="type-small text-[var(--text-dim)] m-0">
          Nothing scored yet — the curve needs at least one assessed skill.
        </p>
      </div>
    );
  }

  const W = 620;
  const H = 300;
  const PAD = { top: 34, right: 64, bottom: 80, left: 64 };
  const plotW = W - PAD.left - PAD.right;
  const plotBottom = H - PAD.bottom;
  const plotH = plotBottom - PAD.top;
  const highest = Math.max(...ranked.map((s) => s.priority), 0.2);
  // Axis top rounded up to the next 0.2 so the ticks are 0.2 / 0.4 / 0.6 rather than
  // 0.16 / 0.32 / 0.47 — a chart nobody can read at a glance is just decoration.
  const max = Math.max(0.4, Math.ceil(highest * 5) / 5);
  const step = ranked.length > 1 ? plotW / (ranked.length - 1) : 0;

  const x = (i: number) => PAD.left + (ranked.length > 1 ? i * step : plotW / 2);
  const y = (v: number) => plotBottom - (v / max) * plotH;

  const points = ranked.map((s, i) => ({ s, cx: x(i), cy: y(s.priority), i }));
  const line = points.map((p) => `${p.cx.toFixed(1)},${p.cy.toFixed(1)}`).join(" ");
  const area = `M ${points[0].cx},${plotBottom} L ${line.replace(/ /g, " L ")} L ${
    points[points.length - 1].cx
  },${plotBottom} Z`;

  const criticalY = y(0.55);
  const gridValues: number[] = [];
  for (let v = 0.2; v <= max + 1e-9; v += 0.2) gridValues.push(Number(v.toFixed(2)));

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full h-auto"
      role="img"
      aria-label={`Priority curve across ${ranked.length} skills, highest first: ${ranked
        .map((s) => `${s.name} ${s.priority.toFixed(2)}`)
        .join(", ")}`}
    >
      <defs>
        <linearGradient id="ios-priority-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.18" />
          <stop offset="100%" stopColor="var(--brand)" stopOpacity="0.01" />
        </linearGradient>
      </defs>

      {/* gridlines */}
      {gridValues.map((v) => (
        <g key={v}>
          <line
            x1={PAD.left}
            x2={W - PAD.right}
            y1={y(v)}
            y2={y(v)}
            stroke="var(--border)"
            strokeDasharray="2 4"
          />
          <text
            x={PAD.left - 8}
            y={y(v) + 3}
            textAnchor="end"
            fontSize="10.5"
            fill="var(--text-dim)"
            fontFamily="var(--font-mono, monospace)"
          >
            {v.toFixed(2)}
          </text>
        </g>
      ))}

      {/* the critical band's lower edge — above this line is where to start */}
      {criticalY > PAD.top && (
        <g>
          <line
            x1={PAD.left}
            x2={W - PAD.right}
            y1={criticalY}
            y2={criticalY}
            stroke="var(--weak)"
            strokeOpacity="0.5"
            strokeDasharray="5 4"
          />
          <text
            x={W - PAD.right}
            y={criticalY - 6}
            textAnchor="end"
            fontSize="10"
            fill="var(--weak)"
            letterSpacing="0.06em"
          >
            CRITICAL ≥ 0.55
          </text>
        </g>
      )}

      <path d={area} fill="url(#ios-priority-fill)" />
      <polyline
        points={line}
        fill="none"
        stroke="var(--brand-strong)"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />

      {points.map(({ s, cx, cy, i }) => {
        const color = BAND_COLOR[s.priority_band] ?? BAND_COLOR.low;
        const r = 4.6 + s.interview_relevance * 3.4;
        return (
          <g key={s.skill_id}>
            <title>
              {`${i + 1}. ${s.name} — priority ${s.priority.toFixed(2)} (${s.priority_band}), gap ${s.gap.toFixed(2)}`}
            </title>
            <circle cx={cx} cy={cy} r={r} fill={color} stroke="var(--surface)" strokeWidth="2" />
            {i < 3 && (
              <text
                x={cx}
                y={cy - r - 7}
                textAnchor="middle"
                fontSize="11.5"
                fontWeight="700"
                fill="var(--text)"
                fontFamily="var(--font-mono, monospace)"
              >
                {i + 1}
              </text>
            )}
            <line
              x1={cx}
              x2={cx}
              y1={plotBottom}
              y2={plotBottom + 4}
              stroke="var(--border-strong)"
            />
            <text
              x={cx}
              y={plotBottom + (i % 2 === 0 ? 17 : 34)}
              textAnchor="middle"
              fontSize="11"
              fill="var(--text-dim)"
            >
              {shorten(s.name)}
            </text>
          </g>
        );
      })}

      {/* axis titles */}
      <text
        x={PAD.left}
        y={PAD.top - 12}
        fontSize="10"
        fill="var(--text-dim)"
        letterSpacing="0.08em"
      >
        TOP 6 BY PRIORITY →
      </text>
      <line
        x1={PAD.left}
        x2={W - PAD.right}
        y1={plotBottom}
        y2={plotBottom}
        stroke="var(--border-strong)"
      />
    </svg>
  );
}
