"use client";

import type { AssessmentState } from "../../contracts/types";

/**
 * Browser-side assessment client. Same contract as `lib/interview.ts`: every call
 * returns `{ ok, data }` or `{ ok: false, status, message }`, so the screen can say why it
 * has nothing instead of showing a spinner forever.
 */
export type Source = "database" | "memory" | "unknown";

export type Result<T> =
  | { ok: true; data: T; source: Source }
  | { ok: false; status: number; message: string };

async function call<T>(path: string, init?: RequestInit): Promise<Result<T>> {
  try {
    const response = await fetch(`/api/assessment/${path}`, {
      ...init,
      headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
      cache: "no-store",
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const detail =
        body && typeof body.detail === "string" ? body.detail : `the API answered ${response.status}`;
      return { ok: false, status: response.status, message: detail };
    }
    const source = (response.headers.get("x-data-source") as Source) ?? "unknown";
    return { ok: true, data: body as T, source };
  } catch {
    return {
      ok: false,
      status: 0,
      message: "the API did not answer — is uvicorn running on :8000?",
    };
  }
}

export function startAssessment(skillId: string): Promise<Result<AssessmentState>> {
  return call<AssessmentState>("start", {
    method: "POST",
    body: JSON.stringify({ skill_id: skillId, mode: "quick", question_total: 3 }),
  });
}

export function submitAssessmentAnswer(
  assessmentId: string,
  answer: string,
): Promise<Result<AssessmentState>> {
  return call<AssessmentState>("answer", {
    method: "POST",
    body: JSON.stringify({ assessment_id: assessmentId, answer }),
  });
}

export function loadAssessment(assessmentId: string): Promise<Result<AssessmentState>> {
  return call<AssessmentState>(encodeURIComponent(assessmentId));
}
