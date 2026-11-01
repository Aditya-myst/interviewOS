const YEAR = 2026;

export default function MarketingFooter() {
  return (
    <footer className="bg-[var(--canvas)] py-12 border-t border-[var(--border)]">
      <div className="max-w-5xl mx-auto px-6 lg:px-12 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex items-center gap-1.5">
          <span className="font-[family-name:var(--font-display)] text-[16px] text-[var(--text)] tracking-[-0.02em]">
            InterviewOS
          </span>
          <span
            className="inline-block size-1.5 rounded-[2px] bg-[var(--brand)]"
            aria-hidden
          />
        </div>

        <p className="type-micro text-[var(--text-dim)] m-0 text-center">
          Built with Next.js, FastAPI, Postgres and open models
        </p>

        <nav aria-label="Legal" className="flex items-center gap-6 type-small">
          <a
            href="/privacy"
            className="text-[var(--text-dim)] hover:text-[var(--text)] transition-colors"
          >
            Privacy
          </a>
          <a
            href="/terms"
            className="text-[var(--text-dim)] hover:text-[var(--text)] transition-colors"
          >
            Terms
          </a>
        </nav>
      </div>

      <div className="max-w-5xl mx-auto px-6 lg:px-12 mt-8">
        <p className="type-micro text-[var(--text-dim)] m-0">
          © {YEAR} InterviewOS. All rights reserved.
        </p>
      </div>
    </footer>
  );
}
