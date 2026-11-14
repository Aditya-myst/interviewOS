import { cn } from "@/lib/utils";

export default function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "skeleton rounded-[12px]",
        className
      )}
    />
  );
}
