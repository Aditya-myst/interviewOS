import { cn } from "@/lib/utils";

const LABELS: Record<string, string> = {
  not_ready: "Not ready yet",
  early: "Early",
  approaching: "Approaching",
  interview_ready: "Interview ready",
};

/**
 * Readiness as a single ring. Hand-drawn SVG on purpose: it is one number, and
 * a charting library for one arc would be 40 kB of JavaScript for nothing.
 */
export default function ReadinessDial({
  value,
  label,
  provisional = false,
  className,
}: {
  value: number;
  label: string;
  provisional?: boolean;
  className?: string;
}) {
  const size = 168;
  const stroke = 12;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value));
  const dash = (pct / 100) * c;

  return (
    <div className={cn("flex flex-col items-center", className)}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          role="img"
          aria-label={`Readiness ${pct} percent — ${LABELS[label] ?? label}`}
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
            stroke="var(--brand)"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${c - dash}`}
          />
        </svg>

        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono tabular-nums text-[38px] leading-none text-[var(--text)]">
            {pct}
            <span className="text-[20px]">%</span>
          </span>
        </div>
      </div>

      <p className="mt-4 mb-1 type-h4 text-[var(--text)]">
        {LABELS[label] ?? label}
      </p>
      <p className="m-0 type-small text-[var(--text-dim)] text-center max-w-[24ch]">
        {provisional
          ? "Provisional — based on partial evidence"
          : "Based on assessed evidence"}
      </p>
    </div>
  );
}
