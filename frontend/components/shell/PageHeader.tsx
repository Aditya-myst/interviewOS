import React from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  actions?: React.ReactNode;
  className?: string;
}

export default function PageHeader({
  eyebrow,
  title,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-col sm:flex-row sm:items-end gap-4 mb-8",
        className
      )}
    >
      <div className="flex-1 min-w-0">
        {eyebrow && (
          <p
            className="text-micro text-[var(--text-dim)] mb-2"
            aria-label={`Section: ${eyebrow}`}
          >
            {eyebrow}
          </p>
        )}
        <h1 className="text-display-3 text-[var(--text)] leading-[0.9]">
          {title}
        </h1>
      </div>

      {actions && (
        <div className="flex items-center gap-3 shrink-0">{actions}</div>
      )}
    </header>
  );
}
