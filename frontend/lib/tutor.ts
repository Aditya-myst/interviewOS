"use client";

/**
 * The tutor's client. The answer shape mirrors `app/tutor/service.py` exactly — focus rows
 * carry the curriculum objective they came from, resources carry catalogue URLs, and
 * citations name the row (or the person's own quote) behind each claim.
 *
 * There is no streaming and no history on the server: one question, one composed answer.
 * That is a design choice, not a shortcut — a chat log that persists would eventually be
 * fed back as "context", and a claim could then appear with no row behind it.
 */
export interface TutorCitation {
  kind: string; // profile | resume_project | assessment_answer | subtopic | resource
  label: string;
  detail?: string | null;
  url?: string | null;
  subtopic_id?: string | null;
}

export interface TutorResource {
  role?: string;
  title?: string;
  url?: string;
  provider?: string;
  kind?: string;
  is_paid?: boolean;
}

export interface TutorFocus {
  subtopic_id: string;
  title: string;
  level: string;
  objective: string;
  why: string;
  resources: TutorResource[];
}

export interface TutorAnswer {
  question: string;
  matched: boolean;
  scope: { skill_id: string; name: string; category: string; in_profile: boolean; source: string } | null;
  standing: string | null;
  lead: string | null;
  focus: TutorFocus[];
  limits: string | null;
  citations: TutorCitation[];
  unknown: { reason: string; can_answer: string[]; next?: string } | null;
  suggestions: string[];
}

export type TutorResult =
  | { ok: true; data: TutorAnswer; source: string }
  | { ok: false; message: string; code?: string };

export async function askTutor(
  question: string,
  options: { skillId?: string; state?: string } = {},
): Promise<TutorResult> {
  const query = options.state ? `?state=${encodeURIComponent(options.state)}` : "";
  try {
    const response = await fetch(`/api/tutor/ask${query}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ question, skill_id: options.skillId }),
      cache: "no-store",
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = body?.detail;
      return {
        ok: false,
        message:
          typeof detail === "string"
            ? detail
            : (detail?.message ?? `the API answered ${response.status}`),
        code: detail?.code,
      };
    }
    return {
      ok: true,
      data: body as TutorAnswer,
      source: response.headers.get("x-data-source") ?? "unknown",
    };
  } catch {
    return { ok: false, message: "the API did not answer — is uvicorn running on :8000?" };
  }
}
