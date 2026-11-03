"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { Check, CircleAlert, FileText, Loader2, Upload, X } from "lucide-react";
import IosButton from "@/components/primitives/IosButton";
import { adviceFor, analyzeJd, uploadResume, type JdAnalysis, type ResumeUpload } from "@/lib/pipeline";

const STEPS = ["Documents", "Assessment", "Roadmap"];

function shorten(text: string, limit: number) {
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length <= limit ? clean : `${clean.slice(0, limit - 1).trimEnd()}…`;
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

type Phase = "idle" | "working" | "done" | "error";

export default function OnboardingPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [jd, setJd] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const [phase, setPhase] = useState<Phase>("idle");
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<{ text: string; code?: string } | null>(null);
  const [resume, setResume] = useState<ResumeUpload | null>(null);
  const [analysis, setAnalysis] = useState<JdAnalysis | null>(null);

  const ready = Boolean(file) && jd.trim().length > 80 && phase !== "working";

  /**
   * Upload, then analyse the JD. Order matters: the backend rescores the stored resume
   * against the JD it just received, so the JD step is what produces the skill rows.
   *
   * Neither call invents success. If the API answers `persisted: false` the parse is real
   * but nothing was stored, and the screen says exactly that instead of sending the user to
   * a dashboard that would show fixture data.
   */
  async function analyze() {
    if (!file) return;
    setPhase("working");
    setError(null);
    setStep(`Reading ${file.name}…`);

    const uploaded = await uploadResume(file);
    if (!uploaded.ok) {
      setPhase("error");
      setError({ text: adviceFor(uploaded.code, uploaded.message), code: uploaded.code });
      setStep(null);
      return;
    }
    setResume(uploaded.data);

    setStep("Matching it against the job description…");
    const jdResult = await analyzeJd(jd.trim());
    if (!jdResult.ok) {
      setPhase("error");
      setError({ text: adviceFor(jdResult.code, jdResult.message), code: jdResult.code });
      setStep(null);
      return;
    }
    setAnalysis(jdResult.data);
    setStep(null);
    setPhase("done");
  }

  return (
    <main className="min-h-screen bg-[var(--canvas)] text-[var(--text)]">
      <header className="border-b border-[var(--border)]">
        <div className="max-w-3xl mx-auto px-6 h-[72px] flex items-center justify-between">
          <Link href="/" className="flex items-center gap-1.5">
            <span className="font-[family-name:var(--font-display)] text-[20px] tracking-[-0.02em]">
              InterviewOS
            </span>
            <span className="inline-block size-2 rounded-[2px] bg-[var(--brand)]" aria-hidden />
          </Link>

          <ol className="hidden sm:flex items-center gap-3 list-none m-0 p-0">
            {STEPS.map((label, i) => (
              <li key={label} className="flex items-center gap-3">
                <span
                  className={`type-micro ${
                    i === 0 ? "text-[var(--text)]" : "text-[var(--text-dim)]"
                  }`}
                >
                  {i + 1}. {label}
                </span>
                {i < STEPS.length - 1 && (
                  <span className="w-6 h-px bg-[var(--border-strong)]" aria-hidden />
                )}
              </li>
            ))}
          </ol>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-6 py-14 lg:py-20">
        <p className="type-micro text-[var(--text-dim)] mb-4">Step 1 of 3</p>
        <h1 className="type-display-3 mb-4">Two documents. That is the whole input.</h1>
        <p className="type-body text-[var(--text-dim)] mb-10 max-w-[54ch]">
          Your resume and the job you are actually targeting. Every skill, gap and
          priority after this is derived from these two — nothing is invented.
        </p>

        {/* Resume dropzone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            const dropped = e.dataTransfer.files?.[0];
            if (dropped) setFile(dropped);
          }}
          className={`rounded-[20px] border-2 border-dashed p-8 text-center transition-colors ${
            dragging
              ? "border-[var(--brand-strong)] bg-[var(--brand-soft)]"
              : "border-[var(--border-strong)] bg-[var(--surface)]"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="sr-only"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />

          {file ? (
            <div className="flex items-center justify-center gap-3">
              <FileText size={20} className="text-[var(--brand-strong)]" aria-hidden />
              <span className="text-left">
                <span className="block font-medium">{file.name}</span>
                <span className="block type-small text-[var(--text-dim)]">
                  {formatSize(file.size)} · ready
                </span>
              </span>
              <button
                type="button"
                onClick={() => setFile(null)}
                aria-label="Remove file"
                className="ml-2 size-9 rounded-full inline-flex items-center justify-center hover:bg-[rgba(13,26,19,0.06)]"
              >
                <X size={16} />
              </button>
            </div>
          ) : (
            <>
              <Upload size={22} className="mx-auto mb-3 text-[var(--text-dim)]" aria-hidden />
              <p className="m-0 mb-1 font-medium">
                Drop your resume here, or{" "}
                <button
                  type="button"
                  onClick={() => inputRef.current?.click()}
                  className="text-[var(--brand-strong)] underline underline-offset-4"
                >
                  browse
                </button>
              </p>
              <p className="m-0 type-small text-[var(--text-dim)]">
                PDF, DOCX or TXT — up to 10 MB
              </p>
            </>
          )}
        </div>

        {/* Job description */}
        <div className="mt-8">
          <div className="flex items-baseline justify-between mb-2">
            <label htmlFor="jd" className="font-medium">
              Job description
            </label>
            <span className="type-small text-[var(--text-dim)] tabular-nums">
              {jd.trim().length} characters
            </span>
          </div>
          <textarea
            id="jd"
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            rows={7}
            placeholder="Paste the full posting — responsibilities, requirements, and the nice-to-haves. Short postings produce shallow gap reports."
            className="w-full rounded-[12px] border border-[var(--border-strong)] bg-[var(--surface)] p-4 type-body outline-none focus:border-[var(--brand-strong)] focus:ring-4 focus:ring-[var(--brand-soft)] resize-y"
          />
          <p className="type-small text-[var(--text-dim)] mt-2">
            Needs at least 80 characters — usually one or two requirement bullets.
          </p>
        </div>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <IosButton variant="primary" size="lg" arrow disabled={!ready} onClick={analyze}>
            {phase === "working" ? "Analysing…" : "Analyze my fit"}
          </IosButton>
          <Link
            href="/"
            className="type-small text-[var(--text-dim)] hover:text-[var(--text)] px-2"
          >
            Back to home
          </Link>
        </div>

        {phase === "working" && (
          <p className="type-small mt-6 flex items-center gap-2 text-[var(--text-dim)]" role="status">
            <Loader2 size={15} className="animate-spin" aria-hidden />
            {step ?? "Working…"}
          </p>
        )}

        {phase === "error" && error && (
          <div className="mt-6 flex items-start gap-2.5 rounded-[12px] border border-[var(--weak)]/40 bg-[var(--weak)]/[0.06] p-4">
            <CircleAlert size={17} className="mt-0.5 shrink-0 text-[var(--weak)]" aria-hidden />
            <div>
              <p className="type-small m-0 font-medium text-[var(--text)]">That did not go through</p>
              <p className="type-small m-0 text-[var(--text-dim)]">{error.text}</p>
              <p className="type-small mt-1.5 mb-0 text-[var(--text-dim)]">
                Nothing was stored.
                {error.code && (
                  <span className="ml-1.5 font-mono text-[11px] text-[var(--text-dim)]">{error.code}</span>
                )}
              </p>
            </div>
          </div>
        )}

        {phase === "done" && resume && <Result resume={resume} analysis={analysis} />}

        {phase === "idle" && (
          <p className="type-small text-[var(--text-dim)] mt-6 max-w-[52ch]">
            {ready
              ? "Both documents are ready. The resume is parsed in this request — nothing is stored until you have seen what it found."
              : "Your file is not uploaded yet — it is sent only when you press Analyse."}
          </p>
        )}
      </div>
    </main>
  );
}

function Result({ resume, analysis }: { resume: ResumeUpload; analysis: JdAnalysis | null }) {
  const skills = resume.skills ?? [];
  const requirements = analysis?.parsed?.requirements ?? [];
  const saved = resume.persisted && (analysis?.persisted ?? false);
  const scored = analysis?.merge?.scored ?? resume.merge?.scored;
  const blocked = analysis?.merge?.reason ?? resume.merge?.reason ?? null;
  // A configured database that said no is a different screen from no database at all:
  // "set DATABASE_URL" would be wrong advice, and the driver's own line is the useful part.
  const persistError = analysis?.persist_error ?? resume.persist_error ?? null;

  return (
    <section className="mt-8 rounded-[18px] border border-[var(--border)] bg-[var(--surface)] p-6">
      <div className="flex flex-wrap items-center gap-3">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--brand)]/12 px-2.5 py-1 type-micro font-medium text-[var(--brand-strong)]">
          <Check size={13} aria-hidden /> {resume.parse_status === "ok" ? "Parsed" : resume.parse_status}
        </span>
        <span className="type-micro text-[var(--text-dim)]">
          {resume.document?.kind?.toUpperCase()} · {resume.document?.pages ?? 1} page
          {(resume.document?.pages ?? 1) === 1 ? "" : "s"} · {resume.document?.chars ?? 0} characters
        </span>
        <span className="type-micro text-[var(--text-dim)]">
          {resume.experience_years != null
            ? `${resume.experience_years} years experience`
            : "experience not stated"}
        </span>
      </div>

      <div className="mt-5 grid gap-5 sm:grid-cols-2">
        <div>
          <p className="type-micro m-0 text-[var(--text-dim)]">Skills found on the resume</p>
          <p className="mt-1 mb-2 font-mono text-[26px] leading-none tabular-nums text-[var(--text)]">
            {skills.length}
          </p>
          <ul className="m-0 flex list-none flex-wrap gap-1.5 p-0">
            {skills.slice(0, 10).map((skill, index) => (
              <li
                key={`${skill.skill_id ?? skill.name ?? index}`}
                className="rounded-full border border-[var(--border-strong)] px-2.5 py-1 type-micro text-[var(--text-dim)]"
              >
                {skill.name ?? skill.skill_id}
              </li>
            ))}
            {skills.length > 10 && (
              <li className="type-micro self-center text-[var(--text-dim)]">+{skills.length - 10} more</li>
            )}
          </ul>
        </div>

        <div>
          <p className="type-micro m-0 text-[var(--text-dim)]">Requirements read from the posting</p>
          <p className="mt-1 mb-2 font-mono text-[26px] leading-none tabular-nums text-[var(--text)]">
            {requirements.length}
          </p>
          <ul className="m-0 grid list-none gap-1.5 p-0">
            {requirements.slice(0, 4).map((row) => (
              <li key={row.skill_id} className="type-small text-[var(--text-dim)]">
                <span className="text-[var(--text)]">{row.name ?? row.skill_id}</span>
                {row.jd_importance != null && (
                  <span className="ml-2 font-mono text-[11px] tabular-nums">
                    {Math.round(row.jd_importance * 100)}
                  </span>
                )}
                {row.evidence?.[0]?.quote && (
                  // The JD's own words, cut to fit: a full paragraph in a list row
                  // overflows the card and pushes the page wider than the viewport.
                  <span className="type-small mt-0.5 block italic text-[var(--text-dim)] line-clamp-2">
                    “{shorten(row.evidence[0].quote, 110)}”
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {saved ? (
        <div className="mt-5 rounded-[12px] border border-[var(--verified)]/35 bg-[var(--brand-soft)] p-4">
          <p className="type-small m-0 font-medium text-[var(--text)]">
            Saved to your profile{typeof scored === "number" ? ` — ${scored} skills scored` : ""}.
          </p>
          <p className="type-small mt-1 mb-0 text-[var(--text-dim)]">
            Your dashboard, gap map and roadmap now read these rows, not fixtures.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href="/dashboard"
              className="inline-flex h-10 items-center rounded-[10px] bg-[var(--brand)] px-3.5 text-sm font-semibold text-[var(--ink-950)]"
            >
              Open my dashboard →
            </Link>
            <Link
              href="/gap-map"
              className="inline-flex h-10 items-center rounded-[10px] border border-[var(--border-strong)] px-3.5 text-sm text-[var(--text-dim)]"
            >
              See the gaps
            </Link>
          </div>
        </div>
      ) : persistError ? (
        <div className="mt-5 rounded-[12px] border border-[var(--weak)]/40 bg-[var(--weak)]/[0.06] p-4">
          <p className="type-small m-0 font-medium text-[var(--text)]">
            Parsed, but the database refused the write.
          </p>
          <p className="type-small mt-1 mb-0 text-[var(--text-dim)]">
            The parse above is real — {skills.length} skills and {requirements.length} requirements
            were read from your documents — but nothing was stored, so your dashboard still shows
            fixtures. What the database said:
          </p>
          <p className="mt-2 mb-0 rounded-[8px] bg-[var(--surface)] px-2.5 py-2 font-mono text-[11.5px] leading-snug text-[var(--text-dim)]">
            {persistError.message}
          </p>
          <p className="type-micro mt-2 mb-0 text-[var(--text-dim)]">{persistError.code}</p>
        </div>
      ) : (
        <div className="mt-5 rounded-[12px] border border-[var(--developing)]/35 bg-[var(--developing)]/[0.07] p-4">
          <p className="type-small m-0 font-medium text-[var(--text)]">
            Parsed, but not saved — no database is configured.
          </p>
          <p className="type-small mt-1 mb-0 text-[var(--text-dim)]">
            The parsing above is real: {skills.length} skills and {requirements.length} requirements were
            read out of your two documents. Writing them to your profile needs `DATABASE_URL` in
            `backend/.env` and the schema from `docs/sql/001_init.sql`. Until then the dashboard shows
            fixtures and says so in its provenance strip.
            {blocked ? ` (${blocked})` : ""}
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href="/dashboard"
              className="inline-flex h-10 items-center rounded-[10px] border border-[var(--border-strong)] px-3.5 text-sm text-[var(--text-dim)]"
            >
              Continue to the dashboard (demo data) →
            </Link>
          </div>
        </div>
      )}

      {!!resume.warnings?.length && (
        <ul className="mt-4 grid list-none gap-1 p-0">
          {resume.warnings.slice(0, 3).map((warning) => (
            <li key={warning} className="type-micro text-[var(--developing)]">
              {warning}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
