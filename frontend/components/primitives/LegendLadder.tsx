import React from "react";
import { cn } from "@/lib/utils";
import type { SkillStatus } from "./SkillPill";

const LADDER_ITEMS: { status: SkillStatus; label: string; description: string }[] = [
  {
    status: "verified",
    label: "Verified",
    description: "Demonstrated under live conditions",
  },
  {
    status: "claimed",
    label: "Claimed",
    description: "Self-reported, not yet tested",
  },
  {
    status: "developing",
    label: "Developing",
    description: "Partial evidence, needs practice",
  },
  {
    status: "needs_revision",
    label: "Needs Revision",
    description: "Shown but with notable gaps",
  },
  {
    status: "weak",
    label: "Weak",
    description: "Significant gap identified",
  },
  {
    status: "unverified",
    label: "Unverified",
    description: "No signal yet",
  },
];

const DOT_STYLES: Record<SkillStatus, string> = {
  verified: "bg-[var(--brand)]",
  claimed: "bg-transparent border-2 border-[var(--text-dim)]",
  developing: "bg-[var(--developing)]",
  needs_revision: "bg-transparent border-2 border-[var(--brand-strong)]",
  weak: "bg-[var(--weak)]",
  unverified: "bg-[var(--text-dim)]",
};

const TEXT_STYLES: Record<SkillStatus, string> = {
  verified: "text-[var(--brand-strong)]",
  claimed: "text-[var(--text-dim)]",
  developing: "text-[var(--developing)]",
  needs_revision: "text-[var(--brand-strong)]",
  weak: "text-[var(--weak)]",
  unverified: "text-[var(--text-dim)]",
};

interface LegendLadderProps {
  className?: string;
}

export default function LegendLadder({ className }: LegendLadderProps) {
  return (
    <div
      role="list"
      aria-label="Skill status legend"
      className={cn("flex flex-col gap-0", className)}
    >
      {LADDER_ITEMS.map((item, i) => (
        <div
          key={item.status}
          role="listitem"
          className="relative flex items-start gap-3 py-2.5 group"
        >
          {/* Vertical connector line */}
          {i < LADDER_ITEMS.length - 1 && (
            <span
              aria-hidden
              className="absolute left-[9px] top-[calc(50%+8px)] bottom-0 w-[1px] bg-[var(--line)]"
            />
          )}

          {/* Dot */}
          <span
            aria-hidden
            className={cn(
              "mt-0.5 size-[18px] rounded-full shrink-0 flex items-center justify-center",
              DOT_STYLES[item.status]
            )}
          >
            {/* Inner dot for hollow states */}
            {(item.status === "claimed" || item.status === "needs_revision") && (
              <span className="size-1.5 rounded-full bg-transparent" />
            )}
          </span>

          {/* Labels */}
          <div className="min-w-0">
            <p className={cn("text-sm font-medium leading-snug", TEXT_STYLES[item.status])}>
              {item.label}
            </p>
            <p className="text-xs text-[var(--text-dim)] leading-snug mt-0.5">
              {item.description}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
