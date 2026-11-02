"use client";

import { motion, useReducedMotion } from "motion/react";

/**
 * Readiness over time, drawn with Motion rather than a chart library.
 *
 * A radar chart answered "what shape is this profile" — which nobody asks. The
 * question a candidate has after a week of prep is "is this going up, and by how
 * much", and that is a line. Motion's `pathLength` draws it once when it scrolls into
 * view, so the eye follows the trend from left to right instead of decoding five
 * overlapping polygons.
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
  const reduced = useReducedMotion();
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
  const line = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.cx.toFixed(1)} ${c.cy.toFixed(1)}`).join(" ");
  const area = `${line} L ${coords[coords.length - 1].cx.toFixed(1)} ${plotBottom} L ${coords[0].cx.toFixed(1)} ${plotBottom} Z`;

  const last = points[points.length - 1].readiness;
  const gridValues = [0, max / 2, max];

  const draw = reduced
    ? {}
    : {
        initial: { pathLength: 0 },
        whileInView: { pathLength: 1 },
        viewport: { once: true, margin: "-60px" },
        transition: { duration: 1.4, ease: "easeInOut" as const },
      };

  return (
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

      <motion.path
        d={area}
        fill="url(#ios-readiness-fill)"
        initial={reduced ? undefined : { opacity: 0 }}
        whileInView={reduced ? undefined : { opacity: 1 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 1, delay: 0.5 }}
      />

      <motion.path
        d={line}
        fill="none"
        stroke="var(--brand-strong)"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
        {...draw}
      />

      {coords.map((c) => (
        <motion.circle
          key={c.date}
          cx={c.cx}
          cy={c.cy}
          r={c.i === coords.length - 1 ? 5.5 : 3.6}
          fill={c.i === coords.length - 1 ? "var(--brand-strong)" : "var(--surface)"}
          stroke="var(--brand-strong)"
          strokeWidth="2"
          initial={reduced ? undefined : { scale: 0, opacity: 0 }}
          whileInView={reduced ? undefined : { scale: 1, opacity: 1 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ type: "spring", stiffness: 300, damping: 20, delay: 0.35 + c.i * 0.11 }}
          style={{ transformOrigin: `${c.cx}px ${c.cy}px` }}
        />
      ))}

      {/* the number that matters, sitting on the last point */}
      <motion.g
        initial={reduced ? undefined : { opacity: 0 }}
        whileInView={reduced ? undefined : { opacity: 1 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.5, delay: 1.25 }}
      >
        <text
          x={coords[coords.length - 1].cx + 9}
          y={coords[coords.length - 1].cy + 4.5}
          fontSize="13"
          fontWeight="700"
          fill="var(--text)"
          fontFamily="var(--font-mono, monospace)"
        >
          {last}%
        </text>
      </motion.g>

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
  );
}
