const ITEMS = ["Next.js", "FastAPI", "Postgres + pgvector", "Gemini + Groq", "SearXNG"];

export default function LogoStrip() {
  return (
    <div className="bg-[var(--canvas)] border-y border-[var(--border)]">
      <div className="max-w-6xl mx-auto px-6 lg:px-10 py-5 flex flex-wrap items-center justify-center gap-x-10 gap-y-3">
        <span className="type-micro text-[var(--text-dim)]">Built with</span>
        {ITEMS.map((label) => (
          <span key={label} className="type-micro text-[var(--text-dim)]/90">
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
