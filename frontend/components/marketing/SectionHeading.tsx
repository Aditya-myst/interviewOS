import React from "react";
import { cn } from "@/lib/utils";

export default function SectionHeading({
  eyebrow,
  title,
  lead,
  tone = "light",
  align = "left",
  className,
}: {
  eyebrow?: string;
  title: React.ReactNode;
  lead?: React.ReactNode;
  tone?: "light" | "ink";
  align?: "left" | "center";
  className?: string;
}) {
  const dim = tone === "ink" ? "text-[var(--on-ink-dim)]" : "text-[var(--text-dim)]";
  const strong = tone === "ink" ? "text-[var(--on-ink)]" : "text-[var(--text)]";
  return (
    <div
      className={cn(
        "mb-10 lg:mb-14",
        align === "center" && "text-center mx-auto max-w-3xl",
        className
      )}
    >
      {eyebrow && <p className={cn("type-micro mb-4", dim)}>{eyebrow}</p>}
      <h2 className={cn("type-display-2", strong)}>{title}</h2>
      {lead && (
        <p
          className={cn(
            "type-body mt-4 max-w-[58ch]",
            dim,
            align === "center" && "mx-auto"
          )}
        >
          {lead}
        </p>
      )}
    </div>
  );
}
