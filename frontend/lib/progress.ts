"use client";

/**
 * Browser-side progress client.
 *
 * Same shape as `lib/assessment.ts` and `lib/interview.ts`: every call resolves to
 * `{ ok: true, data }` or `{ ok: false, status, message }`, so the roadmap can say why a
 * checkbox did not stick instead of silently redrawing the old state.
 */
export type TopicStatus = "not_started" | "in_progress" | "checkpoint_passed" | "done";

export type ProgressResult = {
  topic_id: string;
  status: TopicStatus;
  progress: number;
  plan: { done: number; total: number; percent: number; by_status: Record<string, number> };
};

export type Result<T> =
  | { ok: true; data: T; source: "database" | "unknown" }
  | { ok: false; status: number; message: string };

export async function setTopicStatus(
  topicId: string,
  status: TopicStatus,
): Promise<Result<ProgressResult>> {
  try {
    const response = await fetch(`/api/preparation/topics/${topicId}`, {
      method: "PATCH",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ status }),
      cache: "no-store",
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const detail =
        body && typeof body.detail === "string"
          ? body.detail
          : `the API answered ${response.status}`;
      return { ok: false, status: response.status, message: detail };
    }
    return {
      ok: true,
      data: body as ProgressResult,
      source: (response.headers.get("x-data-source") as "database" | null) ?? "unknown",
    };
  } catch {
    return {
      ok: false,
      status: 0,
      message: "the API did not answer — is uvicorn running on :8000?",
    };
  }
}
