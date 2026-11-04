"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Check, RotateCcw } from "lucide-react";
import { setTopicStatus, type TopicStatus } from "@/lib/progress";
import { cn } from "@/lib/utils";

/**
 * The one write on the roadmap screen.
 *
 * Before this existed, `topics_done` on the dashboard counted `learning_topics` rows and
 * nothing ever wrote one, so the number could not move. The buttons are deliberately
 * explicit — "Mark done" / "Reopen" — rather than a checkbox: a topic is finished when the
 * candidate says so, and undoing it has to be as easy as doing it.
 *
 * Optimistic, then honest: the label flips immediately, and if the write fails the button
 * reverts and says why. A tick that lies is worse than no tick.
 */
export default function TopicProgressControl({
  topicId,
  status,
  disabled = false,
}: {
  topicId: string;
  status: TopicStatus;
  disabled?: boolean;
}) {
  const router = useRouter();
  const [current, setCurrent] = useState<TopicStatus>(status);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [, startTransition] = useTransition();

  const done = current === "done";

  async function apply(next: TopicStatus) {
    const previous = current;
    setCurrent(next);
    setBusy(true);
    setError(null);
    const result = await setTopicStatus(topicId, next);
    setBusy(false);
    if (!result.ok) {
      setCurrent(previous); // never leave a tick that did not stick
      setError(result.message);
      return;
    }
    startTransition(() => router.refresh());
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        disabled={busy || disabled}
        onClick={() => apply(done ? "not_started" : "done")}
        aria-pressed={done}
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 type-micro transition-colors",
          done
            ? "border-[var(--brand)] bg-[var(--brand)] text-[var(--ink-950)]"
            : "border-[var(--border-strong)] text-[var(--text)] hover:border-[var(--brand)]",
          (busy || disabled) && "opacity-60 cursor-not-allowed",
        )}
      >
        {done ? <RotateCcw size={13} aria-hidden /> : <Check size={13} aria-hidden />}
        {done ? "Reopen" : "Mark done"}
      </button>

      {current === "in_progress" && (
        <span className="type-micro text-[var(--developing)]">in progress</span>
      )}

      {error && (
        <span className="type-micro text-[var(--critical)] max-w-[42ch]">
          not saved — {error}
        </span>
      )}
    </div>
  );
}
