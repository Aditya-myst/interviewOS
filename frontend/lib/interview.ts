"use client";

import type {
  InterviewAnswerResult,
  InterviewFeedback,
  InterviewReport,
  InterviewState,
  Transcript,
} from "../../contracts/types";

/**
 * Browser-side interview client. Goes through `app/api/interview/[...path]`, which
 * forwards to FastAPI and preserves the data-source headers.
 *
 * Every call returns `{ data, source, reason }` rather than throwing into the void: the
 * screen has to be able to say *why* it has nothing, and "please try again" is not a
 * reason. Same three outcomes as the server-side client: database, memory, unreachable.
 */
export type Source = "database" | "memory" | "unknown";

export type Result<T> =
  | { ok: true; data: T; source: Source }
  | { ok: false; status: number; message: string };

async function call<T>(path: string, init?: RequestInit): Promise<Result<T>> {
  try {
    const response = await fetch(`/api/interview/${path}`, {
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
      message: "the interview service did not answer — is uvicorn running on :8000?",
    };
  }
}

export function startInterview(questionCount = 5): Promise<Result<InterviewState>> {
  return call<InterviewState>("start", {
    method: "POST",
    body: JSON.stringify({ mode: "jd_based", channel: "text", question_count: questionCount }),
  });
}

export function submitAnswer(
  sessionId: string,
  answer: string,
): Promise<Result<InterviewAnswerResult>> {
  return call<InterviewAnswerResult>("answer", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, answer }),
  });
}

export function loadTranscript(sessionId: string): Promise<Result<Transcript>> {
  return call<Transcript>(`${sessionId}/transcript`);
}

export function loadReport(sessionId: string): Promise<Result<InterviewReport>> {
  return call<InterviewReport>(`${sessionId}/report`);
}

export type { InterviewAnswerResult, InterviewFeedback, InterviewReport, InterviewState };
