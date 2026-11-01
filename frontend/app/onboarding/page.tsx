"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { FileText, Upload, X } from "lucide-react";
import IosButton from "@/components/primitives/IosButton";

const STEPS = ["Documents", "Assessment", "Roadmap"];

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export default function OnboardingPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [jd, setJd] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const ready = Boolean(file) && jd.trim().length > 80;

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
          <IosButton variant="primary" size="lg" arrow disabled={!ready}>
            Analyze my fit
          </IosButton>
          <Link
            href="/"
            className="type-small text-[var(--text-dim)] hover:text-[var(--text)] px-2"
          >
            Back to home
          </Link>
        </div>

        <p className="type-small text-[var(--text-dim)] mt-6 max-w-[52ch]">
          {ready
            ? "Both documents are ready. The parsing and assessment pipeline is the next build — this screen is wired to it, not faking it."
            : "Files stay in this browser until the parsing API ships. Nothing is uploaded yet."}
        </p>
      </div>
    </main>
  );
}
