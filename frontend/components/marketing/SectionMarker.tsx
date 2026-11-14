import { cn } from "@/lib/utils";

/**
 * The page's spine: `01 · THE ACTUAL PROBLEM` in mono, then a hairline that
 * fades out to the right. Every landing section carries one, so the page reads
 * as a numbered document rather than a stack of unrelated blocks.
 */
export default function SectionMarker({
  index,
  label,
  tone = "light",
  className,
}: {
  index: string;
  label: string;
  tone?: "light" | "ink";
  className?: string;
}) {
  const ink = tone === "ink";
  return (
    <div className={cn("flex items-center gap-3 mb-8", className)}>
      <span
        className={cn(
          "type-micro tabular-nums font-mono",
          ink ? "text-[var(--green-300)]" : "text-[var(--brand-strong)]"
        )}
      >
        {index}
      </span>
      <span
        className={cn(
          "type-micro uppercase tracking-[0.14em]",
          ink ? "text-[var(--on-ink-dim)]" : "text-[var(--text-dim)]"
        )}
      >
        {label}
      </span>
      <span
        aria-hidden
        className={cn(
          "h-px flex-1 min-w-8 bg-[linear-gradient(90deg,currentColor,transparent)]",
          ink ? "text-white/25" : "text-[var(--border-strong)]"
        )}
      />
    </div>
  );
}
