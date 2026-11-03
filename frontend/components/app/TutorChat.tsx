"use client";

import { useState } from "react";
import { BookOpen, CircleAlert, ExternalLink, GraduationCap, Loader2, Send, ShieldQuestion } from "lucide-react";
import { askTutor, type TutorAnswer, type TutorCitation } from "@/lib/tutor";

/**
 * The tutor screen. Three promises are enforced in the markup, not just the prose:
 *
 * 1. Every claim shows its source. Citation chips sit under each answer and link to the
 *    catalogue entry or name the profile row — a reader can check the answer instead of
 *    trusting it.
 * 2. "I do not know" is a rendered state. `matched: false` gets a card with the reason and
 *    the topics that *can* be answered, never a paragraph that looks like comprehension.
 * 3. Nothing here moves a level. The footer says so on every answer.
 */
const LEVEL_ORDER = ["beginner", "intermediate", "advanced", "expert"];

function levelIndex(level: string) {
  const index = LEVEL_ORDER.indexOf(level.toLowerCase());
  return index === -1 ? 0 : index;
}

function CitationChips({ citations }: { citations: TutorCitation[] }) {
  const seen = new Set<string>();
  const unique = citations.filter((c) => {
    const key = `${c.kind}:${c.label}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  return (
    <ul className="m-0 mt-3 flex list-none flex-wrap gap-1.5 p-0">
      {unique.map((citation) =>
        citation.kind === "resource" && citation.url ? (
          <li key={`${citation.kind}:${citation.label}`}>
            <a
              href={citation.url}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex max-w-[260px] items-center gap-1 truncate rounded-full border border-[var(--border-strong)] px-2.5 py-1 type-micro text-[var(--text-dim)] hover:border-[var(--brand)] hover:text-[var(--text)]"
            >
              <ExternalLink size={11} className="shrink-0" aria-hidden />
              <span className="truncate">{citation.label}</span>
            </a>
          </li>
        ) : (
          <li
            key={`${citation.kind}:${citation.label}`}
            className={`inline-flex max-w-[340px] items-center gap-1 truncate rounded-full px-2.5 py-1 ${
              citation.kind === "subtopic" ? "type-micro border border-[var(--border-strong)]" : "text-[12.5px]"
            } ${citation.kind === "subtopic" ? "text-[var(--text-dim)]" : "bg-[var(--brand)]/10 text-[var(--brand-strong)]"}`}
            title={citation.detail ?? undefined}
          >
            <span className="truncate">
              {citation.kind === "subtopic" ? citation.label : `“${citation.label}”`}
            </span>
          </li>
        ),
      )}
    </ul>
  );
}

function AnswerCard({ answer }: { answer: TutorAnswer }) {
  if (!answer.matched) {
    return (
      <article className="rounded-[16px] border border-[var(--developing)]/40 bg-[var(--developing)]/[0.06] p-4">
        <p className="m-0 flex items-center gap-2 type-small font-medium text-[var(--text)]">
          <ShieldQuestion size={16} className="text-[var(--developing)]" aria-hidden />
          Not in my sources
        </p>
        <p className="mt-1.5 mb-0 type-small text-[var(--text-dim)]">{answer.unknown?.reason}</p>
        {!!answer.unknown?.can_answer?.length && (
          <>
            <p className="mt-3 mb-1.5 type-micro text-[var(--text-dim)]">I can answer about</p>
            <ul className="m-0 flex list-none flex-wrap gap-1.5 p-0">
              {answer.unknown.can_answer.map((topic) => (
                <li
                  key={topic}
                  className="rounded-full border border-[var(--border-strong)] px-2.5 py-1 type-micro text-[var(--text-dim)]"
                >
                  {topic}
                </li>
              ))}
            </ul>
          </>
        )}
      </article>
    );
  }

  return (
    <article className="rounded-[16px] border border-[var(--border)] bg-[var(--surface)] p-5">
      <header className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--brand)]/12 px-2.5 py-1 type-micro font-medium text-[var(--brand-strong)]">
          <GraduationCap size={13} aria-hidden />
          {answer.scope?.name}
        </span>
        {answer.scope && !answer.scope.in_profile && (
          <span className="type-micro text-[var(--text-dim)]">not on your profile yet</span>
        )}
      </header>

      {answer.standing && (
        <p className="mt-3 mb-0 type-small text-[var(--text)]">{answer.standing}</p>
      )}
      {answer.lead && (
        <p className="mt-1 mb-0 text-[12.5px] leading-snug text-[var(--text-dim)]">{answer.lead}</p>
      )}

      <ol className="mt-4 grid list-none gap-3 p-0">
        {answer.focus.map((node, index) => (
          <li key={node.subtopic_id} className="rounded-[12px] border border-[var(--border)] p-3.5">
            <div className="flex items-baseline gap-2">
              <span className="font-mono text-[11px] tabular-nums text-[var(--text-dim)]">
                0{index + 1}
              </span>
              <h3 className="m-0 text-[15px] font-semibold leading-snug text-[var(--text)]">
                {node.title}
              </h3>
              <span className="ml-auto shrink-0 type-micro text-[var(--text-dim)]">{node.level}</span>
            </div>

            <div className="mt-2 flex gap-1" aria-hidden>
              {LEVEL_ORDER.map((_, step) => (
                <span
                  key={step}
                  className={`h-1 w-5 rounded-full ${
                    step <= levelIndex(node.level) ? "bg-[var(--brand)]" : "bg-[var(--surface-3)]"
                  }`}
                />
              ))}
            </div>

            <p className="mt-2 mb-0 type-small text-[var(--text-dim)]">{node.objective}</p>
            <p className="mt-1 mb-0 text-[12.5px] leading-snug text-[var(--text-dim)]">{node.why}</p>

            {node.resources.length > 0 ? (
              <ul className="mt-2 grid list-none gap-1.5 p-0">
                {node.resources.map((resource) => (
                  <li key={resource.url ?? resource.title}>
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="group inline-flex max-w-full items-center gap-1.5 type-small text-[var(--text)] hover:text-[var(--brand-strong)]"
                    >
                      <BookOpen size={13} className="shrink-0 text-[var(--text-dim)]" aria-hidden />
                      <span className="truncate">{resource.title}</span>
                      <span className="shrink-0 type-micro text-[var(--text-dim)]">
                        {resource.provider}
                        {resource.is_paid ? " · paid" : ""}
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 mb-0 type-micro text-[var(--text-dim)]">
                No curated link for this subtopic — the objective is the curriculum&apos;s own.
              </p>
            )}
          </li>
        ))}
      </ol>

      <CitationChips citations={answer.citations} />

      {answer.limits && (
        <p className="mt-3 mb-0 border-t border-[var(--border)] pt-3 type-micro text-[var(--text-dim)]">
          {answer.limits}
        </p>
      )}
    </article>
  );
}

export default function TutorChat({
  suggestions,
  demoState,
}: {
  suggestions: string[];
  demoState?: string;
}) {
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState<string | null>(null);
  const [answer, setAnswer] = useState<TutorAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const chips = answer?.suggestions?.length ? answer.suggestions : suggestions;

  async function submit(text: string) {
    const trimmed = text.trim();
    if (trimmed.length < 4 || busy) return;
    setBusy(true);
    setError(null);
    setAsked(trimmed);
    const result = await askTutor(trimmed, { state: demoState });
    setBusy(false);
    if (!result.ok) {
      setAnswer(null);
      setError(result.message);
      return;
    }
    setAnswer(result.data);
  }

  return (
    <div className="grid gap-5">
      <section className="rounded-[16px] border border-[var(--border)] bg-[var(--surface)] p-4">
        <label htmlFor="tutor-question" className="type-micro text-[var(--text-dim)]">
          Ask about one skill
        </label>
        <div className="mt-2 flex items-end gap-2">
          <textarea
            id="tutor-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submit(question);
              }
            }}
            rows={2}
            placeholder="How do I close the gap in LLM & RAG?"
            className="min-h-[52px] w-full resize-none rounded-[10px] border border-[var(--border-strong)] bg-[var(--canvas)] px-3 py-2.5 text-[15px] text-[var(--text)] outline-none focus:border-[var(--brand)]"
          />
          <button
            type="button"
            onClick={() => void submit(question)}
            disabled={busy || question.trim().length < 4}
            className="inline-flex h-11 shrink-0 items-center gap-1.5 rounded-[10px] bg-[var(--brand)] px-4 text-sm font-semibold text-[var(--ink-950)] disabled:pointer-events-none disabled:bg-[var(--surface-3)] disabled:text-[var(--text-dim)]"
          >
            {busy ? <Loader2 size={15} className="animate-spin" aria-hidden /> : <Send size={15} aria-hidden />}
            Ask
          </button>
        </div>

        {chips.length > 0 && (
          <ul className="m-0 mt-3 flex list-none flex-wrap gap-1.5 p-0">
            {chips.slice(0, 3).map((chip) => (
              <li key={chip}>
                <button
                  type="button"
                  onClick={() => {
                    setQuestion(chip);
                    void submit(chip);
                  }}
                  className="rounded-full border border-[var(--border-strong)] px-3 py-1.5 text-[12.5px] text-[var(--text-dim)] hover:border-[var(--brand)] hover:text-[var(--text)]"
                >
                  {chip}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {asked && (
        <p className="m-0 type-micro text-[var(--text-dim)]">
          You asked: <span className="text-[var(--text)]">{asked}</span>
        </p>
      )}

      {error && (
        <div className="flex items-start gap-2.5 rounded-[12px] border border-[var(--weak)]/40 bg-[var(--weak)]/[0.06] p-4">
          <CircleAlert size={17} className="mt-0.5 shrink-0 text-[var(--weak)]" aria-hidden />
          <div>
            <p className="m-0 type-small font-medium text-[var(--text)]">The tutor could not answer</p>
            <p className="m-0 type-small text-[var(--text-dim)]">{error}</p>
          </div>
        </div>
      )}

      {answer ? (
        <AnswerCard answer={answer} />
      ) : (
        !error && (
          <div className="rounded-[16px] border border-dashed border-[var(--border-strong)] p-6 text-center">
            <p className="m-0 type-small text-[var(--text-dim)]">
              Answers are composed from your own profile rows, the curriculum subtopics and the
              curated catalogue — not written freehand. Ask about a skill and you will see the
              rows it used.
            </p>
          </div>
        )
      )}
    </div>
  );
}
