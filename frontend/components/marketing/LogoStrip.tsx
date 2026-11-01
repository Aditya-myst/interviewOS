
export default function LogoStrip() {
  const items = [
    "NEXT.JS",
    "FASTAPI",
    "POSTGRES + PGVECTOR",
    "GEMINI + GROQ",
    "DUCKDUCKGO / SEARXNG",
  ];
  return (
    <section className="border-t border-b border-[var(--border)] py-7">
      <div className="max-w-5xl mx-auto px-6 lg:px-12 flex justify-between text-micro text-[var(--text-dim)]">
        {items.map((item) => (
          <span key={item}>{item}</span>
        ))}
      </div>
    </section>
  );
}
