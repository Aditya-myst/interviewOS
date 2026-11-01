"use client";

import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import Section from "./Section";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import IosButton from "@/components/primitives/IosButton";
import SkillPill, { type SkillStatus } from "@/components/primitives/SkillPill";

/** Mirrors contracts/fixtures/dashboard.json `coverage` (values 0-100 for the radar). */
const COVERAGE = [
  { category: "Language", verified: 70, developing: 30, unverified: 0 },
  { category: "Backend", verified: 20, developing: 60, unverified: 20 },
  { category: "Data", verified: 30, developing: 45, unverified: 25 },
  { category: "Infra", verified: 0, developing: 25, unverified: 75 },
  { category: "AI", verified: 25, developing: 40, unverified: 35 },
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

        {/* Coverage radar */}
        <Reveal delay={120} className="h-full">
          <div className="card-surface p-5 sm:p-6 h-full flex flex-col">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div>
                <p className="type-micro text-[var(--text-dim)] mb-1">Skill coverage</p>
                <p className="type-small text-[var(--text-dim)] m-0">
                  Share of skills in each state, by category
                </p>
              </div>
              <span className="font-mono text-[13px] text-[var(--text-dim)] tabular-nums">
                2 / 9 verified
              </span>
            </div>

            <div className="mx-auto w-full max-w-[330px] aspect-square my-2" aria-hidden>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={COVERAGE} outerRadius="66%">
                  <PolarGrid stroke="rgba(13,26,19,0.12)" />
                  <PolarAngleAxis
                    dataKey="category"
                    tick={{ fill: "var(--text-dim)", fontSize: 11 }}
                  />
                  <Radar
                    name="Verified"
                    dataKey="verified"
                    stroke="var(--brand-strong)"
                    fill="var(--brand)"
                    fillOpacity={0.22}
                    strokeWidth={2}
                    animationDuration={900}
                  />
                  <Radar
                    name="Developing"
                    dataKey="developing"
                    stroke="var(--developing)"
                    fill="var(--developing)"
                    fillOpacity={0.1}
                    strokeWidth={1.5}
                    strokeDasharray="4 3"
                    animationDuration={1100}
                  />
                  <Radar
                    name="Unverified"
                    dataKey="unverified"
                    stroke="var(--unverified)"
                    fill="var(--unverified)"
                    fillOpacity={0.06}
                    strokeWidth={1.5}
                    strokeDasharray="2 3"
                    animationDuration={1300}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            <ul className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-4 pt-4 border-t border-[var(--border)] list-none p-0 text-xs text-[var(--text-dim)]">
              {[
                ["Verified", "var(--brand)"],
                ["Developing", "var(--developing)"],
                ["Unverified", "var(--unverified)"],
              ].map(([label, color]) => (
                <li key={label} className="flex items-center gap-1.5">
                  <span
                    className="size-2 rounded-full"
                    style={{ background: color }}
                    aria-hidden
                  />
                  {label}
                </li>
              ))}
            </ul>

            <p className="type-small text-[var(--text-dim)] mt-4 pt-4 border-t border-[var(--border)] m-0">
              Infra is the least proven block: three of its four skills have never
              been tested.
            </p>

            {/* screen-reader equivalent of the chart */}
            <table className="sr-only">
              <caption>Skill coverage by category</caption>
              <thead>
                <tr>
                  <th scope="col">Category</th>
                  <th scope="col">Verified</th>
                  <th scope="col">Developing</th>
                  <th scope="col">Unverified</th>
                </tr>
              </thead>
              <tbody>
                {COVERAGE.map((c) => (
                  <tr key={c.category}>
                    <td>{c.category}</td>
                    <td>{c.verified}%</td>
                    <td>{c.developing}%</td>
                    <td>{c.unverified}%</td>
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
