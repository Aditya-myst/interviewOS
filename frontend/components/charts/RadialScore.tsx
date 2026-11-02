import { cn } from "@/lib/utils";

/**
 * One ring, one number. Hand-drawn SVG: a charting library for a single arc is
 * 40 kB of JavaScript for a shape we can express in six lines.
 */
export default function RadialScore({
  value,
  label,
  size = 132,
  stroke = 10,
  tone = "brand",
  className,
}: {
  value: number;
  label?: string;
  size?: number;
  stroke?: number;
  tone?: "brand" | "developing" | "weak";
  className?: string;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const dash = (pct / 100) * c;
  const color =
    tone === "developing"
      ? "var(--developing)"
      : tone === "weak"
        ? "var(--weak)"
        : "var(--brand)";

  return (
    <div className={cn("relative shrink-0", className)} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label={`${pct} percent${label ? ` — ${label}` : ""}`}
        className="-rotate-90"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="var(--surface-3)"
          strokeWidth={stroke}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c - dash}`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-mono tabular-nums text-[26px] leading-none text-[var(--text)]">
          {pct}
          <span className="text-[13px]">%</span>
        </span>
        {label && (
          // A label like "interview ready" is wider than the ring, and a label that
          // spills over the stroke looks like a rendering bug. Constrained and wrapped.
          <span className="type-micro text-[var(--text-dim)] mt-1 max-w-[76%] text-center leading-[1.15] tracking-[0.04em] uppercase">
            {label}
          </span>
        )}
      </div>
    </div>
  );
}
