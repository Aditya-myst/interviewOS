import { cn } from "@/lib/utils";

export type Stat = {
  label: string;
  value: string;
  sub?: string;
  tone?: "default" | "good" | "warn";
};

export default function StatTiles({
  stats,
  className,
}: {
  stats: Stat[];
  className?: string;
}) {
  return (
    <dl className={cn("grid grid-cols-2 gap-3 m-0", className)}>
      {stats.map((s) => (
        <div
          key={s.label}
          className="rounded-[12px] border border-[var(--border)] bg-[var(--surface)] px-4 py-3 min-h-[78px]"
        >
          <dt className="type-micro text-[var(--text-dim)] m-0">{s.label}</dt>
          <dd
            className={cn(
              "m-0 mt-1 font-mono tabular-nums text-[24px] leading-none",
              s.tone === "good" && "text-[var(--verified)]",
              s.tone === "warn" && "text-[var(--developing)]",
              (!s.tone || s.tone === "default") && "text-[var(--text)]"
            )}
          >
            {s.value}
          </dd>
          {s.sub && (
            <dd className="m-0 mt-1 type-small text-[var(--text-dim)]">{s.sub}</dd>
          )}
        </div>
      ))}
    </dl>
  );
}
