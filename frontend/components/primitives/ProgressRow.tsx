import React from "react";
import { cn } from "@/lib/utils";

interface ProgressRowProps {
  title: string;
  current: number;
  total: number;
  className?: string;
}

export default function ProgressRow({
  title,
  current,
  total,
  className,
}: ProgressRowProps) {
  const pct = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;

  return (
    <div className={cn("flex flex-col gap-2 py-3 border-b border-[var(--line)] last:border-b-0", className)}>
      <div className="flex items-center justify-between gap-4">
        <span className="text-small text-[var(--text)] leading-snug">{title}</span>
        <span className="text-mono-value text-xs text-[var(--text-dim)] shrink-0">
          {current}
          <span className="text-[var(--line-strong)] mx-0.5">/</span>
          {total}
        </span>
      </div>

      {/* Track */}
      <div
        className="h-[6px] w-full rounded-[999px] bg-[var(--surface-3)] overflow-hidden"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${title}: ${current} of ${total}`}
      >
        <div
          className="h-full rounded-[999px] bg-[var(--brand)] transition-[width] duration-[150ms] ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
