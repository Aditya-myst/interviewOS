import type { Dashboard } from "../../../contracts/types";
import { formatDate } from "@/lib/fixtures";

const MODE_LABEL: Record<string, string> = {
  beginner_practice: "Beginner practice",
  intermediate_technical: "Intermediate technical",
  advanced_technical: "Advanced technical",
  resume_based: "Resume-based",
  jd_based: "JD-based",
  full_mock: "Full mock",
};

export default function InterviewTable({
  interviews,
}: {
  interviews: Dashboard["interviews"];
}) {
  if (interviews.length === 0) {
    return (
      <p className="type-small text-[var(--text-dim)] m-0">
        No mock interviews yet. Your first one takes about twenty minutes.
      </p>
    );
  }

  return (
    <div className="-mx-5 sm:mx-0 overflow-x-auto">
      <table className="w-full min-w-[460px] border-collapse text-left">
        <thead>
          <tr className="border-b border-[var(--border)]">
            {["Mode", "Channel", "Score", "Length", "Date"].map((h) => (
              <th
                key={h}
                scope="col"
                className="type-micro text-[var(--text-dim)] py-2 pr-4 font-medium"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {interviews.map((s) => (
            <tr key={s.session_id} className="border-b border-[var(--border)] last:border-0">
              <td className="py-3 pr-4 type-small">{MODE_LABEL[s.mode] ?? s.mode}</td>
              <td className="py-3 pr-4 type-small text-[var(--text-dim)]">
                {s.channel}
              </td>
              <td className="py-3 pr-4">
                <span
                  className={`font-mono tabular-nums text-sm ${
                    (s.score ?? 0) >= 70
                      ? "text-[var(--verified)]"
                      : (s.score ?? 0) >= 50
                        ? "text-[var(--developing)]"
                        : "text-[var(--weak)]"
                  }`}
                >
                  {s.score ?? "—"}
                </span>
              </td>
              <td className="py-3 pr-4 type-small text-[var(--text-dim)] tabular-nums">
                {s.duration_minutes ? `${s.duration_minutes} min` : "—"}
              </td>
              <td className="py-3 type-small text-[var(--text-dim)] tabular-nums">
                {formatDate(s.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
