import React from "react";
import { cn } from "@/lib/utils";

export type BandLevel = "critical" | "high" | "medium" | "low";

interface BandCardProps {
  title: string;
  count: number;
  band: BandLevel;
  description?: string;
  className?: string;
}

const BAND_CONFIG: Record<
  BandLevel,
  { accentColor: string; bgColor: string; borderColor: string; label: string }
> = {
  critical: {
    accentColor: "text-[var(--weak)]",
    bgColor: "bg-[var(--weak)]/8",
    borderColor: "border-[var(--weak)]/30",
    label: "Critical",
  },
  high: {
    accentColor: "text-[var(--developing)]",
    bgColor: "bg-[var(--developing)]/8",
    borderColor: "border-[var(--developing)]/30",
    label: "High",
  },
  medium: {
    accentColor: "text-[var(--brand-strong)]",
    bgColor: "bg-[var(--brand)]/10",
    borderColor: "border-[var(--green-700)]/40",
    label: "Medium",
  },
  low: {
    accentColor: "text-[var(--text-dim)]",
    bgColor: "bg-[var(--surface-2)]",
    borderColor: "border-[var(--line)]",
    label: "Low",
  },
};

export default function BandCard({
  title,
  count,
  band,
  description,
  className,
}: BandCardProps) {
  const cfg = BAND_CONFIG[band];

  return (
    <div
      className={cn(
        "flex items-center gap-4 p-4 rounded-[20px] border",
        cfg.bgColor,
        cfg.borderColor,
        className
      )}
    >
      {/* Count */}
      <span
        className={cn(
          "type-mono-value text-3xl font-black leading-none shrink-0 tabular-nums",
          cfg.accentColor
        )}
        aria-label={`${count} ${band} priority items`}
      >
        {count}
      </span>

      <div className="min-w-0">
        <p className="text-sm font-semibold text-[var(--text)] leading-snug">
          {title}
        </p>
        <p className={cn("type-micro mt-0.5", cfg.accentColor)}>{cfg.label}</p>
        {description && (
          <p className="text-xs text-[var(--text-dim)] mt-1 leading-snug">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}
