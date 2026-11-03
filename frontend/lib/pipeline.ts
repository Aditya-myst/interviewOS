"use client";

/**
 * Browser client for the parsing pipeline.
 *
 * `uploadResume` sends the file untouched — the browser sets the multipart boundary and
 * the route handler forwards the bytes, so nothing re-encodes a PDF on the way.
 *
 * Both calls come back with `persisted`, which is the field the screen needs: without a
 * database the parse is real but the profile is not saved, and the UI must say that rather
 * than claim a profile it does not have.
 */
export type Source = "database" | "pipeline" | "unknown";

export type Result<T> =
  | { ok: true; data: T; source: Source }
  | { ok: false; status: number; message: string; code?: string };

export interface ResumeSkill {
  skill_id?: string;
  name?: string;
  category?: string;
  level?: string;
  quote?: string | null;
}

export interface ResumeUpload {
  parse_status: string;
  persisted: boolean;
  resume_id?: string | null;
  user_source?: string | null;
  document?: { filename: string; kind: string; chars: number; pages: number; sha256: string };
  stats?: Record<string, number>;
  experience_years?: number | null;
  experience_basis?: string | null;
  warnings?: string[];
  skills?: ResumeSkill[];
  merge?: { scored: number; reason: string | null };
  /** Present when the schema refused the write. The parse above is still real. */
  persist_error?: { code: string; message: string };
}

export interface JdAnalysis {
  parse_status: string;
  persisted: boolean;
  jd_id?: string | null;
  parsed?: {
    title?: string | null;
    company?: string | null;
    role?: string | null;
    seniority?: string | null;
    min_years_experience?: number | null;
    /** Each row is a skill the posting asks for, with the quote that proves it. */
    requirements?: Array<{
      skill_id: string;
      name?: string;
      requirement_type?: string;
      jd_importance?: number;
      expected_level?: string;
      evidence?: Array<{ quote?: string; section?: string }>;
    }>;
  };
  merge?: { scored: number; reason: string | null };
  /** Present when the schema refused the write. The parse above is still real. */
  persist_error?: { code: string; message: string };
}

/**
 * The API speaks in codes ("pdf_unreadable", "startxref not found"); a person needs a
 * sentence that tells them what to do next. The raw reason is kept as `message` so the
 * UI can still show it in small print.
 */
const ADVICE: Record<string, string> = {
  pdf_unreadable:
    "We could not read that PDF — it is scanned images or damaged. Export a text PDF, DOCX or TXT and try again.",
  unsupported_type: "That file type is not supported. Upload a PDF, DOCX, TXT or Markdown file.",
  empty_file: "That file is empty. Pick the document you actually want analysed.",
  too_large: "That file is larger than the 10 MB limit.",
  encrypted: "That PDF is password-protected. Remove the password, then upload it.",
  jd_too_short:
    "The job description is too short. Paste the responsibilities and requirements sections.",
  user_unresolved: "The API could not resolve which user to save to. Check the auth or demo user setting.",
};

export function adviceFor(code: string | undefined, fallback: string): string {
  return (code && ADVICE[code]) || fallback;
}

async function call<T>(path: string, init: RequestInit): Promise<Result<T>> {
  try {
    const response = await fetch(`/api/pipeline/${path}`, { ...init, cache: "no-store" });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = body?.detail;
      const message =
        typeof detail === "string"
          ? detail
          : typeof detail?.message === "string"
            ? detail.message
            : `the API answered ${response.status}`;
      return { ok: false, status: response.status, message, code: detail?.code };
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

export function uploadResume(file: File): Promise<Result<ResumeUpload>> {
  const form = new FormData();
  form.append("file", file, file.name);
  // No content-type header: the browser must set it, boundary and all.
  return call<ResumeUpload>("resume/upload", { method: "POST", body: form });
}

export function analyzeJd(text: string): Promise<Result<JdAnalysis>> {
  return call<JdAnalysis>("jd/analyze", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text }),
  });
}
