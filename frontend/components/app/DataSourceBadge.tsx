import { Database, FileJson, Unplug } from "lucide-react";
import { describeReason, type DataSource } from "@/lib/api";

/**
 * The provenance strip. Every screen that renders numbers carries one.
 *
 * Green: these numbers came out of Postgres, for this user, just now.
 * Amber: the API answered but had no rows, so you are looking at its contract
 *        fixture — the screen still shows a real shape, and says so.
 * Red:   the API did not answer at all; this is fixture data read from disk.
 *
 * It renders the endpoint it actually asked for, so "is this dummy data?" is a
 * question the screen answers itself, in one line, without a screenshot of a
 * database client.
 */
const STYLE: Record<DataSource, { wrap: string; dot: string; label: string }> = {
  database: {
    wrap: "border-[var(--verified)]/35 bg-[var(--brand-soft)] text-[var(--brand-strong)]",
    dot: "bg-[var(--verified)]",
    label: "Postgres",
  },
  fixture: {
    wrap: "border-[var(--developing)]/35 bg-[var(--developing)]/10 text-[var(--developing)]",
    dot: "bg-[var(--developing)]",
    label: "Fixture",
  },
  unreachable: {
    wrap: "border-[var(--weak)]/35 bg-[var(--weak)]/8 text-[var(--weak)]",
    dot: "bg-[var(--weak)]",
    label: "Offline",
  },
};

const ICON = { database: Database, fixture: FileJson, unreachable: Unplug } as const;

export default function DataSourceBadge({
  source,
  endpoint,
  reason,
  className = "",
}: {
  source: DataSource;
  endpoint: string;
  reason?: string | null;
  className?: string;
}) {
  const style = STYLE[source];
  const Icon = ICON[source];

  const detail =
    source === "database"
      ? `${endpoint} · live rows`
      : source === "fixture"
        ? `${endpoint} · ${describeReason(reason ?? "no_rows") || "no rows"}`
        : `${endpoint} · API not reachable, showing saved fixtures`;

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-[var(--radius-pill)] border px-3 py-1 type-micro ${style.wrap} ${className}`}
      title={detail}
    >
      <span className={`size-1.5 rounded-full ${style.dot}`} aria-hidden />
      <Icon size={12} aria-hidden />
      <span className="font-medium">{style.label}</span>
      <span className="opacity-80 font-mono">{detail}</span>
    </span>
  );
}
