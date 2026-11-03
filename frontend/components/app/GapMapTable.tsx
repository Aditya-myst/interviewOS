"use client";

import { Fragment, useMemo, useState } from "react";
import Link from "next/link";
import { ChevronDown, Quote } from "lucide-react";
import type { CandidateSkill, PriorityBand } from "../../../contracts/types";
import SkillPill from "@/components/primitives/SkillPill";

const BANDS: Array<{ key: "all" | PriorityBand; label: string }> = [
  { key: "all", label: "All" },
  { key: "critical", label: "Critical" },
  { key: "high", label: "High" },
  { key: "medium", label: "Medium" },
  { key: "low", label: "Low" },
];

const BAND_STYLE: Record<string, string> = {
  critical: "bg-[var(--weak)]/12 text-[var(--weak)]",
  high: "bg-[var(--developing)]/12 text-[var(--developing)]",
  medium: "bg-[var(--brand)]/12 text-[var(--brand-strong)]",
  low: "bg-[var(--surface-2)] text-[var(--text-dim)]",
};

const EVIDENCE_LABEL: Record<string, string> = {
  resume_skill_list: "resume · skill list",
  resume_project: "resume · project",
  resume_experience: "resume · experience",
  assessment_answer: "assessment answer",
  interview_answer: "interview answer",
  user_correction: "your correction",
};

export default function GapMapTable({ skills }: { skills: CandidateSkill[] }) {
  const [band, setBand] = useState<"all" | PriorityBand>("all");
  const [open, setOpen] = useState<string | null>(null);

  const counts = useMemo(() => {
    const c: Record<string, number> = { all: skills.length };
    for (const s of skills) c[s.priority_band] = (c[s.priority_band] ?? 0) + 1;
    return c;
  }, [skills]);

  const rows = useMemo(
    () =>
      skills
        .filter((s) => band === "all" || s.priority_band === band)
        .sort((a, b) => b.priority - a.priority),
    [skills, band]
  );

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        {BANDS.map((b) => {
          const active = band === b.key;
          const n = counts[b.key] ?? 0;
          return (
            <button
              key={b.key}
              type="button"
              onClick={() => setBand(b.key)}
              aria-pressed={active}
              className={`inline-flex items-center gap-2 h-9 px-3 rounded-[999px] type-small font-medium border transition-colors ${
                active
                  ? "bg-[var(--ink-950)] text-[var(--on-ink)] border-[var(--ink-950)]"
                  : "bg-[var(--surface)] text-[var(--text-dim)] border-[var(--border)] hover:text-[var(--text)]"
              }`}
            >
              {b.label}
              <span
                className={`tabular-nums text-[11px] ${
                  active ? "text-[var(--on-ink-dim)]" : "text-[var(--text-dim)]"
                }`}
              >
                {n}
              </span>
            </button>
          );
        })}
      </div>

      {/* Desktop table */}
      <div className="hidden md:block card-surface overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse text-left">
            <thead>
              <tr className="bg-[var(--surface-2)]">
                {["Skill", "Category", "Status", "Level", "Priority", "Evidence"].map(
                  (h) => (
                    <th
                      key={h}
                      scope="col"
                      className={`type-micro text-[var(--text-dim)] px-4 py-2.5 font-medium ${
                        h === "Priority" ? "w-[120px]" : ""
                      } ${h === "Evidence" ? "w-[110px]" : ""}`}
                    >
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => {
                const isOpen = open === s.skill_id;
                const hasEvidence = s.evidence.length > 0;
                return (
                  <Fragment key={s.skill_id}>
                    <tr
                      id={`skill-${s.skill_id}`}
                      className="border-t border-[var(--border)] align-top scroll-mt-24 target:bg-[var(--brand-soft)]/50"
                    >
                      <td className="px-4 py-3.5">
                        <span className="font-medium">{s.name}</span>
                        <span
                          title={s.explanation}
                          className="block type-small text-[var(--text-dim)] mt-0.5 max-w-[46ch] line-clamp-2"
                        >
                          {s.explanation}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 type-small text-[var(--text-dim)]">
                        {s.category ?? "—"}
                      </td>
                      <td className="px-4 py-3.5">
                        <SkillPill
                          label={s.status.replace("_", " ")}
                          status={s.status}
                        />
                      </td>
                      <td className="px-4 py-3.5 type-small text-[var(--text-dim)] whitespace-nowrap">
                        {s.expected_level && s.expected_level !== "none"
                          ? s.expected_level
                          : "not in JD"}
                        {" → "}
                        {s.verified_level && s.verified_level !== "none"
                          ? s.verified_level
                          : "unproven"}
                      </td>
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        <span
                          className={`inline-block px-2 py-1 rounded-[999px] text-[11px] font-semibold tracking-[0.06em] ${
                            BAND_STYLE[s.priority_band]
                          }`}
                        >
                          {s.priority_band.toUpperCase()}
                        </span>
                        <span className="block font-mono text-[11px] text-[var(--text-dim)] mt-1 tabular-nums">
                          {s.priority.toFixed(2)}
                        </span>
                      </td>
                      <td className="px-4 py-3.5">
                        {hasEvidence ? (
                          <button
                            type="button"
                            onClick={() => setOpen(isOpen ? null : s.skill_id)}
                            aria-expanded={isOpen}
                            className="inline-flex items-center gap-1.5 type-small font-medium text-[var(--brand-strong)] hover:underline underline-offset-4"
                          >
                            {s.evidence.length} quote
                            {s.evidence.length > 1 ? "s" : ""}
                            <ChevronDown
                              size={14}
                              aria-hidden
                              className={`transition-transform ${
                                isOpen ? "rotate-180" : ""
                              }`}
                            />
                          </button>
                        ) : (
                          <span className="type-small text-[var(--text-dim)]">
                            none yet
                          </span>
                        )}
                      </td>
                    </tr>

                    {isOpen && (
                      <tr className="bg-[var(--surface)]">
                        <td colSpan={6} className="px-4 py-4">
                          <EvidenceList evidence={s.evidence} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

      </div>

      {/* Mobile cards — a 6-column table at 390px is unreadable, so the same
          rows render as stacked cards instead of horizontal scroll. */}
      <ul className="md:hidden list-none m-0 p-0 space-y-3">
        {rows.map((s) => {
          const isOpen = open === s.skill_id;
          return (
            <li
              key={s.skill_id}
              id={`skill-${s.skill_id}`}
              className="card-surface p-4 scroll-mt-24 target:bg-[var(--brand-soft)]/50"
            >
              <div className="flex items-start justify-between gap-3 mb-1.5">
                <h3 className="type-h4 m-0">{s.name}</h3>
                <span
                  className={`shrink-0 px-2 py-1 rounded-[999px] text-[11px] font-semibold tracking-[0.06em] ${
                    BAND_STYLE[s.priority_band]
                  }`}
                >
                  {s.priority_band.toUpperCase()}
                </span>
              </div>

              <div className="flex flex-wrap items-center gap-2 mb-2">
                <SkillPill label={s.status.replace("_", " ")} status={s.status} />
                <span className="type-small text-[var(--text-dim)]">
                  {s.category ?? "—"} ·{" "}
                  {s.expected_level && s.expected_level !== "none"
                    ? s.expected_level
                    : "not in JD"}{" "}
                  →{" "}
                  {s.verified_level && s.verified_level !== "none"
                    ? s.verified_level
                    : "unproven"}
                </span>
              </div>

              <p className="m-0 type-small text-[var(--text-dim)]">{s.explanation}</p>

              <div className="mt-3 flex items-center gap-4">
                <span className="font-mono text-[11px] text-[var(--text-dim)] tabular-nums">
                  priority {s.priority.toFixed(2)}
                </span>
                {/* The ladder is how a claim becomes evidence without a full mock interview. */}
                <Link
                  href={`/assessment?skill=${s.skill_id}`}
                  className="type-small font-medium text-[var(--brand-strong)] hover:underline"
                >
                  {s.status === "verified" ? "Re-assess" : "Assess in 3 questions"} →
                </Link>
                {s.evidence.length > 0 ? (
                  <button
                    type="button"
                    onClick={() => setOpen(isOpen ? null : s.skill_id)}
                    aria-expanded={isOpen}
                    className="ml-auto inline-flex items-center gap-1.5 type-small font-medium text-[var(--brand-strong)]"
                  >
                    {s.evidence.length} quote{s.evidence.length > 1 ? "s" : ""}
                    <ChevronDown
                      size={14}
                      aria-hidden
                      className={`transition-transform ${isOpen ? "rotate-180" : ""}`}
                    />
                  </button>
                ) : (
                  <span className="ml-auto type-small text-[var(--text-dim)]">
                    no evidence yet
                  </span>
                )}
              </div>

              {isOpen && (
                <div className="mt-3 pt-3 border-t border-[var(--border)]">
                  <EvidenceList evidence={s.evidence} />
                </div>
              )}
            </li>
          );
        })}
        {rows.length === 0 && (
          <li className="card-surface p-6 text-center type-small text-[var(--text-dim)]">
            No skills in the {band} band.
          </li>
        )}
      </ul>

      {rows.length === 0 && (
        <p className="hidden md:block m-0 px-4 py-8 text-center type-small text-[var(--text-dim)]">
          No skills in the {band} band.
        </p>
      )}
    </div>
  );
}

function EvidenceList({ evidence }: { evidence: CandidateSkill["evidence"] }) {
  return (
    <ul className="list-none m-0 p-0 space-y-3">
      {evidence.map((e, i) => (
        <li key={i} className="flex gap-3">
          <Quote
            size={15}
            className="mt-1 shrink-0 text-[var(--brand-strong)]"
            aria-hidden
          />
          <div>
            <p className="m-0 type-small text-[var(--text)]">
              &ldquo;{e.quote}&rdquo;
            </p>
            <p className="m-0 mt-1 type-micro text-[var(--text-dim)]">
              {EVIDENCE_LABEL[e.type] ?? e.type}
              {e.section ? ` · ${e.section}` : ""}
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}
