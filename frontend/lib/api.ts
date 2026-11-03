/**
 * The one place the frontend talks to FastAPI.
 *
 * Until now every screen read `contracts/fixtures` directly, so nothing on screen
 * had ever been produced by the backend. This module changes that: a page asks for
 * a payload and gets back the payload *and* where it came from, because the API
 * says so itself in `X-Data-Source` / `X-Fallback-Reason`.
 *
 * Three honest outcomes, never conflated:
 *
 *   database     rows came out of Postgres for this user
 *   fixture      the API answered, but served its contract fixture (with a reason)
 *   unreachable  the API did not answer at all, so this page is showing fixtures
 *                it read from disk — the screen must say so
 *
 * `endpoint` travels with the payload so a badge can print exactly what was asked,
 * which is the difference between a demo and a claim.
 */
import { cache } from "react";
import type { Dashboard, InterviewReport, Roadmap, SkillProfile } from "../../contracts/types";
import {
  dashboardFixture,
  interviewReportFixture,
  roadmapFixture,
  skillProfileFixture,
} from "./fixtures";

export type DataSource = "database" | "fixture" | "unreachable";

export type ApiPayload<T> = {
  data: T;
  source: DataSource;
  /** `X-Fallback-Reason` when the API served a fixture; null when it served rows. */
  reason: string | null;
  /** the path that was requested, e.g. `/v1/analytics/dashboard` */
  endpoint: string;
};

/** Override in `.env.local` when the API is not on the default port. */
const BASE = (process.env.INTERVIEWOS_API_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

/**
 * A demo should fail over to a labelled fixture rather than hang, but a remote
 * Postgres pooler can take seconds to hand out its first connection, and a false
 * "offline" is worse than a slow page. Ten seconds, then say so.
 */
const TIMEOUT_MS = 10_000;

/**
 * `unreachable` covers three different things — a network error, a timeout and a
 * non-2xx response — and printing one sentence for all three is how a 500 hides.
 */
export function describeUnreachable(reason: string | null): string {
  if (!reason) return "the API did not answer";
  if (reason === "TimeoutError") return `no answer within ${TIMEOUT_MS / 1000}s`;
  if (reason.startsWith("http_")) return `the API answered ${reason.slice(5)}`;
  return reason;
}

const REASON_TEXT: Record<string, string> = {
  no_db: "the API has no database configured",
  no_profile: "no profile for this user yet",
  no_rows: "this account has no scored skills yet",
  db_error: "the API's query failed — check the uvicorn console",
};

/** Human sentence for a fallback reason, so a screen never prints `db_error`. */
export function describeReason(reason: string | null): string {
  if (!reason) return "";
  return REASON_TEXT[reason] ?? reason;
}

async function getJson<T>(path: string, fallback: T): Promise<ApiPayload<T>> {
  try {
    const response = await fetch(`${BASE}${path}`, {
      // The whole point of this screen is that it reflects the database right now.
      cache: "no-store",
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });

    if (!response.ok) {
      return {
        data: fallback,
        source: "unreachable",
        reason: `http_${response.status}`,
        endpoint: path,
      };
    }

    const data = (await response.json()) as T;
    return {
      data,
      source: response.headers.get("x-data-source") === "database" ? "database" : "fixture",
      reason: response.headers.get("x-fallback-reason"),
      endpoint: path,
    };
  } catch (error) {
    return {
      data: fallback,
      source: "unreachable",
      reason: error instanceof Error ? error.name : "unknown_error",
      endpoint: path,
    };
  }
}

/** `?state=` is a demo switch; the API applies it only on the fixture path. */
function demoQuery(state?: string): string {
  return state && state !== "populated" ? `?state=${encodeURIComponent(state)}` : "";
}

/* `cache` wraps a function per render pass, so a page and a layout asking for the
 * same endpoint share one HTTP call instead of two. */
export const loadDashboard = cache(
  (state?: string): Promise<ApiPayload<Dashboard>> =>
    getJson<Dashboard>(`/v1/analytics/dashboard${demoQuery(state)}`, dashboardFixture)
);

export const loadSkillProfile = cache(
  (state?: string): Promise<ApiPayload<SkillProfile>> =>
    getJson<SkillProfile>(`/v1/skills/profile${demoQuery(state)}`, skillProfileFixture)
);

export const loadRoadmap = cache(
  (state?: string): Promise<ApiPayload<Roadmap>> =>
    getJson<Roadmap>(`/v1/learning/roadmap${demoQuery(state)}`, roadmapFixture)
);

/**
 * The report is the one screen that can be reached two ways: from a session that just
 * ended (`?session=<id>`, live) or from the nav with nothing in hand (recorded fixture).
 * The API decides, and says which it did in `X-Data-Source` — the page prints that
 * rather than implying a live session exists.
 */
export const loadInterviewReport = cache(
  (sessionId: string): Promise<ApiPayload<InterviewReport>> =>
    getJson<InterviewReport>(
      `/v1/interview/${encodeURIComponent(sessionId)}/report`,
      interviewReportFixture,
    ),
);
