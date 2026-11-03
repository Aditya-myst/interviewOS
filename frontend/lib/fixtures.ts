/**
 * Fixture access for phases 3–4, before the API exists.
 *
 * These are the same JSON files the backend will return (contracts/fixtures/),
 * so a page built on them needs no rework when the endpoints land — only the
 * `loadFixture` call changes for a `fetch`.
 *
 * They are read from disk rather than imported: Turbopack refuses to resolve
 * modules outside the app root, and copying 9 KB of JSON into frontend/ would
 * create a second source of truth. Types still come from contracts/types.ts,
 * which is erased at compile time.
 */
import { readFileSync } from "node:fs";
import path from "node:path";
import type { Dashboard, InterviewReport, SkillProfile, Roadmap } from "../../contracts/types";

const CANDIDATES = [
  path.join(process.cwd(), "..", "contracts", "fixtures"),
  path.join(process.cwd(), "contracts", "fixtures"),
];

function loadFixture<T>(name: string): T {
  const dir = CANDIDATES.find((d) => {
    try {
      readFileSync(path.join(d, name));
      return true;
    } catch {
      return false;
    }
  });

  if (!dir) {
    throw new Error(
      `Fixture ${name} not found. Looked in:\n${CANDIDATES.join("\n")}\n` +
        "Run the frontend from frontend/ inside the repo so ../contracts resolves."
    );
  }

  return JSON.parse(readFileSync(path.join(dir, name), "utf8")) as T;
}

export const dashboardFixture = loadFixture<Dashboard>("dashboard.json");
export const skillProfileFixture = loadFixture<SkillProfile>("skill_profile.json");
export const roadmapFixture = loadFixture<Roadmap>("roadmap.json");
export const interviewReportFixture = loadFixture<InterviewReport>("interview_report.json");

/**
 * The clock every fixture is written against. Relative labels ("assessed 3d
 * ago") must be computed from this, not from the wall clock, or the demo will
 * claim a 2026 fixture was assessed 300 days ago.
 */
export const FIXTURE_TODAY = "2026-11-01T00:00:00Z";

/** The `?state=` variants the UI must survive. */
export type DemoState = "populated" | "empty" | "degraded" | "loading";

export function parseState(raw: string | string[] | undefined): DemoState {
  const v = Array.isArray(raw) ? raw[0] : raw;
  return v === "empty" || v === "degraded" || v === "loading"
    ? v
    : "populated";
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    timeZone: "UTC",
  }).format(new Date(iso));
}
