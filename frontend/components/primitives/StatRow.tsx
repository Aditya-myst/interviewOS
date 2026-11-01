import React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatRowProps {
  label: string;
  value: string | number;
  delta?: number; // positive = up (green), negative = down (red)
  unit?: string;
  className?: string;
}

export default function StatRow({
  label,
  value,
  delta,
  unit,
  className,
}: StatRowProps) {
  const hasDelta = delta !== undefined && delta !== 0;
  const isUp = delta !== undefined && delta > 0;

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-4 py-3",
        "border-b border-[var(--line)] last:border-b-0",
        className
      )}
    >
      {/* Label */}
      <span className="text-small text-[var(--text-dim)] leading-snug">
        {label}
      </span>

      {/* Value + delta */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-mono-value text-sm font-medium text-[var(--text)]">
          {value}
          {unit && (
            <span className="text-[var(--text-dim)] ml-0.5 text-xs">
              {unit}
            </span>
          )}
        </span>

        {hasDelta && (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-[999px] text-xs font-medium text-mono-value",
              isUp
                ? "bg-[var(--green-500)]/15 text-[var(--green-400)]"
                : "bg-[var(--weak)]/15 text-[var(--weak)]"
            )}
            aria-label={`${isUp ? "Up" : "Down"} ${Math.abs(delta!)}`}
          >
            {isUp ? (
              <TrendingUp size={10} strokeWidth={2} />
            ) : (
              <TrendingDown size={10} strokeWidth={2} />
            )}
            {Math.abs(delta!)}
          </span>
        )}
      </div>
    </div>
  );
}
