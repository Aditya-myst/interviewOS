"use client";

import { useInView, usePrefersReducedMotion } from "@/lib/useInView";

/**
 * Readiness over time.
 *
 * A radar chart answered "what shape is this profile" — which nobody asks. The
 * question a candidate has after a week of prep is "is this going up, and by how
 * much", and that is a line. It draws itself when it scrolls into view, so the eye
 * follows the trend from left to right instead of decoding five overlapping polygons.
 *
 * The data is the recorded `readiness_history` from contracts/fixtures/dashboard.json —
 * seven real points from a sample run, not a curve imagined for the landing page.
 */
export type ReadinessPoint = { date: string; readiness: number };

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function shortDate(iso: string): string {
  const [, m, d] = iso.split("-").map(Number);
  return `${d} ${MONTHS[(m ?? 1) - 1]}`;
}

export default function ReadinessLine({
  points,
  className = "",
}: {
  points: ReadinessPoint[];
  className?: string;
}) {
  const reduced = usePrefersReducedMotion();
  const { ref, inView } = useInView<HTMLDivElement>("-60px");
  const shown = inView || reduced;

  if (points.length < 2) {
    return (
      <p className="type-small text-[var(--text-dim)]">
        One measurement so far — the trend needs a second session.
      </p>
    );
  }

  const W = 440;
  const H = 236;
  const PAD = { top: 30, right: 46, bottom: 34, left: 30 };
  const plotW = W - PAD.left - PAD.right;
  const plotBottom = H - PAD.bottom;
  const plotH = plotBottom - PAD.top;

  const values = points.map((p) => p.readiness);
  const highest = Math.max(...values);
  const max = Math.max(40, Math.ceil((highest + 6) / 10) * 10);
  const step = plotW / (points.length - 1);

  const x = (i: number) => PAD.left + i * step;
  const y = (v: number) => plotBottom - (v / max) * plotH;

  const coords = points.map((p, i) => ({ ...p, cx: x(i), cy: y(p.readiness), i }));
  const lineD = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.cx.toFixed(1)} ${c.cy.toFixed(1)}`).join(" ");
  const areaD = `${lineD} L ${coords[coords.length - 1].cx.toFixed(1)} ${plotBottom} L ${coords[0].cx.toFixed(1)} ${plotBottom} Z`;

  const last = points[points.length - 1].readiness;
  const gridValues = [0, max / 2, max];

  return (
    <div ref={ref}>
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className={`w-full h-auto ${className}`}
        role="img"
        aria-label={`Readiness from ${shortDate(points[0].date)} to ${shortDate(
          points[points.length - 1].date,
        )}: ${points.map((p) => `${shortDate(p.date)} ${p.readiness}%`).join(", ")}`}
      >
        <defs>
          <linearGradient id="ios-readiness-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.26" />
            <stop offset="100%" stopColor="var(--brand)" stopOpacity="0.02" />
          </linearGradient>
        </defs>

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
              y={y(v) + 3.5}
              textAnchor="end"
              fontSize="11"
              fill="var(--text-dim)"
              fontFamily="var(--font-mono, monospace)"
            >
              {Math.round(v)}
            </text>
          </g>
        ))}

        <path
          d={areaD}
          fill="url(#ios-readiness-fill)"
          style={{
            opacity: shown ? 1 : 0,
            transition: reduced ? undefined : "opacity 1000ms ease 500ms",
          }}
        />

        <path
          d={lineD}
          fill="none"
          stroke="var(--brand-strong)"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          pathLength={1}
          strokeDasharray={1}
          style={{
            strokeDashoffset: shown ? 0 : 1,
            transition: reduced ? undefined : "stroke-dashoffset 1400ms ease-in-out",
          }}
        />

        {coords.map((c) => {
          const isLast = c.i === coords.length - 1;
          const delay = reduced ? 0 : 350 + c.i * 110;
          return (
            <circle
              key={c.date}
              cx={c.cx}
              cy={c.cy}
              r={isLast ? 5.5 : 3.6}
              fill={isLast ? "var(--brand-strong)" : "var(--surface)"}
              stroke="var(--brand-strong)"
              strokeWidth="2"
              style={{
                opacity: shown ? 1 : 0,
                transform: shown ? "scale(1)" : "scale(0.3)",
                transformOrigin: `${c.cx}px ${c.cy}px`,
                transition: reduced
                  ? undefined
                  : `opacity 400ms ease ${delay}ms, transform 400ms cubic-bezier(0.34,1.56,0.64,1) ${delay}ms`,
              }}
            />
          );
        })}

        {/* the number that matters, sitting on the last point */}
        <text
          x={coords[coords.length - 1].cx + 9}
          y={coords[coords.length - 1].cy + 4.5}
          fontSize="13"
          fontWeight="700"
          fill="var(--text)"
          fontFamily="var(--font-mono, monospace)"
          style={{
            opacity: shown ? 1 : 0,
            transition: reduced ? undefined : "opacity 500ms ease 1250ms",
          }}
        >
          {last}%
        </text>

        <line
          x1={PAD.left}
          x2={W - PAD.right}
          y1={plotBottom}
          y2={plotBottom}
          stroke="var(--border-strong)"
        />
        {coords.map((c) =>
          c.i === 0 || c.i === coords.length - 1 ? (
            <text
              key={`d-${c.date}`}
              x={c.cx}
              y={plotBottom + 17}
              textAnchor={c.i === 0 ? "start" : "end"}
              fontSize="11"
              fill="var(--text-dim)"
            >
              {shortDate(c.date)}
            </text>
          ) : null,
        )}
      </svg>
    </div>
  );
}
