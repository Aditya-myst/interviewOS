import { cn } from "@/lib/utils";

export default function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "animate-pulse rounded-[12px] bg-[var(--surface-3)]/70",
        className
      )}
    />
  );
}
