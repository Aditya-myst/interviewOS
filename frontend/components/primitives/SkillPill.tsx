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

const STATUS_CONFIG: Record<
  SkillStatus,
  {
    dotColor: string;
    textColor: string;
    bg: string;
    border: string;
    dotStyle?: string;
    borderStyle?: string;
  }
> = {
  weak: {
    dotColor: "bg-[var(--weak)]",
    textColor: "text-[var(--weak)]",
    bg: "bg-[var(--weak)]/10",
    border: "border-transparent",
  },
  developing: {
    dotColor: "bg-[var(--developing)]",
    textColor: "text-[var(--developing)]",
    bg: "bg-[var(--developing)]/10",
    border: "border-transparent",
  },
  verified: {
    dotColor: "bg-[var(--green-500)]",
    textColor: "text-[var(--green-400)]",
    bg: "bg-[var(--green-500)]/10",
    border: "border-transparent",
  },
  unverified: {
    dotColor: "bg-[var(--text-dim)]",
    textColor: "text-[var(--text-dim)]",
    bg: "bg-[var(--ink-800)]",
    border: "border-transparent",
  },
  claimed: {
    dotColor: "bg-[var(--text-dim)]",
    textColor: "text-[var(--text-dim)]",
    bg: "bg-transparent",
    border: "border-[var(--line-strong)]",
  },
  needs_revision: {
    dotColor: "bg-transparent border-2 border-[var(--green-500)]",
    textColor: "text-[var(--green-400)]",
    bg: "bg-[var(--green-500)]/10",
    border: "border-[var(--green-700)]",
    borderStyle: "border-dashed",
  },
};

export default function SkillPill({ label, status, className }: SkillPillProps) {
  const cfg = STATUS_CONFIG[status];

  return (
    <span
      role="status"
      aria-label={`${label}: ${status.replace("_", " ")}`}
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[999px] border text-xs font-medium",
        "transition-all duration-[150ms] ease-out",
        cfg.bg,
        cfg.border,
        cfg.textColor,
        cfg.borderStyle,
        className
      )}
    >
      {/* Status dot */}
      <span
        aria-hidden
        className={cn(
          "size-1.5 rounded-full shrink-0",
          status === "needs_revision"
            ? "size-2 rounded-full border-2 border-[var(--green-500)] bg-transparent"
            : cfg.dotColor
        )}
      />
      {label}
    </span>
  );
}
