const ITEMS = [
  "Next.js",
  "FastAPI",
  "Postgres + pgvector",
  "Gemini + Groq",
  "SearXNG",
  "rubric scoring",
  "HTTP-checked resources",
];

/**
 * A slow tape, not a logo wall: the stack scrolls past at 46s a loop, which is
 * slow enough to read as texture and quiet enough to ignore. The second copy of
 * the list is aria-hidden so screen readers hear the stack exactly once.
 */
export default function LogoStrip() {
  const row = (copy: number) => (
    <div className="tape shrink-0 items-center gap-8 pr-8" aria-hidden={copy === 1}>
      {ITEMS.map((label) => (
        <span key={label} className="flex shrink-0 items-center gap-8">
          <span className="type-micro whitespace-nowrap text-[var(--text-dim)]">
            {label}
          </span>
          <span aria-hidden className="size-1 rotate-45 bg-[var(--border-strong)]" />
        </span>
      ))}
    </div>
  );

  return (
    <div className="relative overflow-hidden border-y border-[var(--border)] bg-[var(--surface)]/60">
      <div className="tape-mask flex overflow-hidden py-4">
        {row(0)}
        {row(1)}
      </div>
      <span className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-[linear-gradient(90deg,var(--canvas),transparent)]" aria-hidden />
      <span className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-[linear-gradient(270deg,var(--canvas),transparent)]" aria-hidden />
      <span className="sr-only">Built with: {ITEMS.join(", ")}</span>
    </div>
  );
}
