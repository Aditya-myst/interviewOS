import React from "react";
import { cn } from "@/lib/utils";

export type SkillStatus =
  | "weak"
  | "developing"
  | "verified"
  | "unverified"
  | "claimed"
  | "needs_revision";

interface SkillPillProps {
  label: string;
  status: SkillStatus;
  className?: string;
}

/**
 * Contrast-corrected for the cream canvas.
 * Rule: no colour below 4.5:1 is used for text. `--green-400` is a
 * decorative tone and is never used as a label colour here.
 */
const STATUS_CONFIG: Record<
  SkillStatus,
  { dot: string; text: string; bg: string; border: string }
> = {
  weak: {
    dot: "bg-[var(--weak)]",
    text: "text-[var(--weak)]",
    bg: "bg-[var(--weak)]/10",
    border: "border-[var(--weak)]/25",
  },
  developing: {
    dot: "bg-[var(--developing)]",
    text: "text-[var(--developing)]",
    bg: "bg-[var(--developing)]/10",
    border: "border-[var(--developing)]/25",
  },
  verified: {
    dot: "bg-[var(--brand)]",
    text: "text-[var(--brand-strong)]",
    bg: "bg-[var(--brand)]/12",
    border: "border-[var(--brand)]/30",
  },
  unverified: {
    dot: "bg-[var(--unverified)]",
    text: "text-[var(--unverified)]",
    bg: "bg-[var(--surface-2)]",
    border: "border-[var(--border)]",
  },
  claimed: {
    dot: "bg-[var(--unverified)]",
    text: "text-[var(--text-dim)]",
    bg: "bg-transparent",
    border: "border-[var(--border-strong)]",
  },
  needs_revision: {
    dot: "bg-transparent border-2 border-[var(--brand-strong)]",
    text: "text-[var(--brand-strong)]",
    bg: "bg-[var(--brand)]/8",
    border: "border-dashed border-[var(--brand-strong)]/45",
  },
};

export default function SkillPill({ label, status, className }: SkillPillProps) {
  const cfg = STATUS_CONFIG[status];

  return (
    <span
      role="status"
      aria-label={`${label}: ${status.replace("_", " ")}`}
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[999px] border text-xs font-medium",
        "transition-all duration-[150ms] ease-out",
        cfg.bg,
        cfg.border,
        cfg.text,
        className
      )}
    >
      <span
        aria-hidden
        className={cn(
          "size-1.5 rounded-full shrink-0",
          status === "needs_revision" && "size-2",
          cfg.dot
        )}
      />
      {label}
    </span>
  );
}
