import React from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  /** One sentence under the title: what this screen is for, in plain words. */
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}

export default function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <header className={cn("mb-8", className)}>
      <div className="flex flex-col sm:flex-row sm:items-end gap-4">
        <div className="flex-1 min-w-0">
          {eyebrow && (
            <p
              className="type-micro flex items-center gap-2 text-[var(--text-dim)] mb-2"
              aria-label={`Section: ${eyebrow}`}
            >
              <span
                aria-hidden
                className="inline-block size-1.5 rounded-full bg-[var(--brand)] dot-live"
              />
              {eyebrow}
            </p>
          )}
          <h1 className="type-display-3 text-[var(--text)] leading-[0.9] animate-rise">
            {title}
          </h1>
        </div>

        {actions && (
          <div className="flex items-center gap-3 shrink-0 animate-fade">{actions}</div>
        )}
      </div>

      {description && (
        <p className="type-lede mt-4 mb-0 animate-fade">{description}</p>
      )}

      {/* A rule that fades out: it closes the header without cutting the page in half. */}
      <div aria-hidden className="rule-fade mt-6" />
    </header>
  );
}
