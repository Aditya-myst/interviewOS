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
import type { Dashboard, Roadmap, SkillProfile } from "../../contracts/types";
import { dashboardFixture, roadmapFixture, skillProfileFixture } from "./fixtures";

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

/** Short on purpose: a demo should fail over to a labelled fixture, not hang. */
const TIMEOUT_MS = 4000;

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

export function loadDashboard(state?: string): Promise<ApiPayload<Dashboard>> {
  return getJson<Dashboard>(`/v1/analytics/dashboard${demoQuery(state)}`, dashboardFixture);
}

export function loadSkillProfile(state?: string): Promise<ApiPayload<SkillProfile>> {
  return getJson<SkillProfile>(`/v1/skills/profile${demoQuery(state)}`, skillProfileFixture);
}

export function loadRoadmap(state?: string): Promise<ApiPayload<Roadmap>> {
  return getJson<Roadmap>(`/v1/learning/roadmap${demoQuery(state)}`, roadmapFixture);
}
