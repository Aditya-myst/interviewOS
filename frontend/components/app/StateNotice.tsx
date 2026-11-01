import { AlertTriangle, Info } from "lucide-react";

/**
 * Degraded-mode banner. When the model is unavailable the deterministic parser
 * still produces a usable profile — the UI says so instead of failing, which is
 * the behaviour we demo on purpose.
 */
export default function StateNotice({
  kind = "info",
  title,
  children,
}: {
  kind?: "info" | "warn";
  title: string;
  children?: React.ReactNode;
}) {
  const Icon = kind === "warn" ? AlertTriangle : Info;
  return (
    <div
      role="status"
      className={`flex items-start gap-3 rounded-[12px] border px-4 py-3 ${
        kind === "warn"
          ? "border-[var(--developing)]/35 bg-[var(--developing)]/8"
          : "border-[var(--border)] bg-[var(--surface)]"
      }`}
    >
      <Icon
        size={18}
        className={`mt-0.5 shrink-0 ${
          kind === "warn" ? "text-[var(--developing)]" : "text-[var(--text-dim)]"
        }`}
        aria-hidden
      />
      <div>
        <p className="m-0 type-small font-medium text-[var(--text)]">{title}</p>
        {children && (
          <p className="m-0 mt-0.5 type-small text-[var(--text-dim)]">{children}</p>
        )}
      </div>
    </div>
  );
}
