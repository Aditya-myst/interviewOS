"use client";

import Section from "./Section";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import IosButton from "@/components/primitives/IosButton";
import SkillPill, { type SkillStatus } from "@/components/primitives/SkillPill";
import ReadinessLine from "@/components/charts/ReadinessLine";

/** Verbatim from contracts/fixtures/dashboard.json `readiness_history`, a recorded run. */
const READINESS = [
  { date: "2026-10-26", readiness: 26 },
  { date: "2026-10-27", readiness: 29 },
  { date: "2026-10-28", readiness: 33 },
  { date: "2026-10-29", readiness: 42 },
  { date: "2026-10-30", readiness: 38 },
  { date: "2026-10-31", readiness: 40 },
  { date: "2026-11-01", readiness: 42 },
];

const ROWS: Array<{
  skill: string;
  status: SkillStatus;
  band: "CRITICAL" | "HIGH" | "LOW";
  why: string;
}> = [
  {
    skill: "LLM & RAG",
    status: "developing",
    band: "CRITICAL",
    why: "Required at expert level; your evidence is beginner-level work on one project.",
  },
  {
    skill: "FastAPI",
    status: "weak",
    band: "HIGH",
    why: "Listed on your resume; the assessment found no practical evidence.",
  },
  {
    skill: "React",
    status: "claimed",
    band: "LOW",
    why: "Strong on your resume, but this job never asks for it.",
  },
];

const BAND_STYLE: Record<string, string> = {
  CRITICAL: "bg-[var(--weak)]/12 text-[var(--weak)]",
  HIGH: "bg-[var(--developing)]/12 text-[var(--developing)]",
  LOW: "bg-[var(--surface-2)] text-[var(--text-dim)]",
};

export default function SampleReport() {
  return (
    <Section id="sample-report" tone="surface">
      <SectionHeading
        eyebrow="Sample report"
        title={
          <>
            Priorities, with the
            <br className="hidden sm:block" /> reason attached.
          </>
        }
        lead="Every row is generated from three inputs — your resume, the job description, and what the assessment actually proved. Nothing is guessed, and nothing is unordered."
      />

      <div className="grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-6 lg:gap-8 items-stretch">
        {/* Priority table */}
        <Reveal>
          <div className="card-surface overflow-hidden h-full flex flex-col">
            <div className="px-5 sm:px-6 py-4 border-b border-[var(--border)] flex items-center justify-between gap-4">
              <h3 className="type-h3 m-0">Where to start</h3>
              <span className="type-micro text-[var(--text-dim)]">Northwind Labs · AI Engineer</span>
            </div>

            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="bg-[var(--surface-2)]">
                  {["Skill", "Status", "Priority", "Why"].map((h) => (
                    <th
                      key={h}
                      scope="col"
                      className={`type-micro text-[var(--text-dim)] px-5 sm:px-6 py-2.5 ${
                        h === "Skill" ? "w-[20%]" : ""
                      } ${h === "Status" ? "w-[22%]" : ""} ${
                        h === "Priority" ? "w-[16%]" : ""
                      } ${h === "Status" || h === "Priority" ? "hidden md:table-cell" : ""}`}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {ROWS.map((r) => (
                  <tr key={r.skill} className="border-b border-[var(--border)] last:border-0">
                    <td className="px-5 sm:px-6 py-4 align-top font-semibold">{r.skill}</td>
                    <td className="px-5 sm:px-6 py-4 align-top hidden md:table-cell">
                      <SkillPill label={r.status.replace("_", " ")} status={r.status} />
                    </td>
                    <td className="px-5 sm:px-6 py-4 align-top hidden md:table-cell">
                      <span
                        className={`inline-block px-2 py-1 rounded-[999px] text-[11px] font-semibold tracking-[0.06em] ${BAND_STYLE[r.band]}`}
                      >
                        {r.band}
                      </span>
                    </td>
                    <td className="px-5 sm:px-6 py-4 align-top type-small text-[var(--text-dim)] max-w-[34ch]">
                      {r.why}
                      <div className="md:hidden mt-2">
                        <SkillPill label={r.status.replace("_", " ")} status={r.status} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="mt-auto px-5 sm:px-6 py-4 border-t border-[var(--border)] flex items-center justify-between gap-4">
              <p className="text-xs text-[var(--text-dim)] m-0">
                Prerequisites ordered by interview impact, not by syllabus order.
              </p>
              <IosButton href="#how-it-works" variant="secondary" size="sm" arrow>
                How this is scored
              </IosButton>
            </div>
          </div>
        </Reveal>

        {/* Readiness trend */}
        <Reveal delay={120} className="h-full">
          <div className="card-surface p-5 sm:p-6 h-full flex flex-col">
            <div className="flex items-start justify-between gap-3 mb-3">
              <div>
                <p className="type-micro text-[var(--text-dim)] mb-1">Readiness trend</p>
                <p className="type-small text-[var(--text-dim)] m-0">
                  Every session re-scores the graph, so this line moves for a reason.
                </p>
              </div>
              <span className="font-mono text-[12px] tabular-nums whitespace-nowrap rounded-full bg-[var(--brand)]/12 px-2.5 py-1 text-[var(--brand-strong)]">
                +16 pts · 7 sessions
              </span>
            </div>

            <div className="my-1">
              <ReadinessLine points={READINESS} />
            </div>

            <p className="type-small text-[var(--text-dim)] mt-auto pt-4 border-t border-[var(--border)] m-0">
              Recorded sessions, 26 October to 1 November. The drop on 30 October is a
              real measurement — an interview session failed to confirm two claimed
              skills — not a smoothing artefact, and it is left in the line.
            </p>

            {/* screen-reader equivalent of the chart */}
            <table className="sr-only">
              <caption>Readiness by session date</caption>
              <thead>
                <tr>
                  <th scope="col">Date</th>
                  <th scope="col">Readiness</th>
                </tr>
              </thead>
              <tbody>
                {READINESS.map((r) => (
                  <tr key={r.date}>
                    <td>{r.date}</td>
                    <td>{r.readiness}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Reveal>
      </div>
    </Section>
  );
}
