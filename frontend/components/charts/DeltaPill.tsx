import { ArrowDownRight, ArrowUpRight } from "lucide-react";

export default function DeltaPill({
  value,
  suffix = "",
  label,
}: {
  value: number;
  suffix?: string;
  label?: string;
}) {
  const up = value >= 0;
  const Icon = up ? ArrowUpRight : ArrowDownRight;
  return (
    <span
      className={`inline-flex items-center gap-1 type-small font-medium ${
        up ? "text-[var(--verified)]" : "text-[var(--weak)]"
      }`}
    >
      <Icon size={13} aria-hidden />
      <span className="tabular-nums">
        {up ? "+" : ""}
        {value}
        {suffix}
      </span>
      {label && <span className="text-[var(--text-dim)] font-normal">{label}</span>}
    </span>
  );
}
