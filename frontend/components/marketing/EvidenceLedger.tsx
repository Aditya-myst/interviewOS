type Verdict = "verified" | "partial" | "not proven" | "not asked";

/**
 * The hero artifact: an evidence ledger, not a pair of overlapping cards.
 *
 * It says the one thing the product actually does — a resume claim meets a
 * rubric verdict — and it says it in the product's own vocabulary. Rows arrive
 * on the paper stagger; each verdict lands a beat later with a stepped stamp.
 * Every figure here is labelled SAMPLE, because it is one.
 */
const ROWS: Array<{
  claim: string;
  level: string;
  verdict: Verdict;
  note: string;
}> = [
  {
    claim: "Python",
    level: "applied",
    verdict: "verified",
    note: "3 of 3 answered",
  },
  {
    claim: "FastAPI",
    level: "practical",
    verdict: "not proven",
    note: "listed on the resume only",
  },
  {
    claim: "LLM & RAG",
    level: "conceptual",
    verdict: "partial",
    note: "no eval set, no metric",
  },
  {
    claim: "System design",
    level: "applied",
    verdict: "not asked",
    note: "never reached in this session",
  },
];

/* Lightened for ink. The page's own status tokens are tuned for paper and go
   muddy at #0d1a13, so the stamps get their -300 siblings. */
const STAMP: Record<Verdict, { text: string; ring: string; bg: string }> = {
  verified: {
    text: "text-[#86efac]",
    ring: "border-[#86efac]/45",
    bg: "bg-[#86efac]/10",
  },
  partial: {
    text: "text-[#fcd34d]",
    ring: "border-[#fcd34d]/45",
    bg: "bg-[#fcd34d]/10",
  },
  "not proven": {
    text: "text-[#fca5a5]",
    ring: "border-[#fca5a5]/45",
    bg: "bg-[#fca5a5]/10",
  },
  "not asked": {
    text: "text-[var(--on-ink-dim)]",
    ring: "border-white/20",
    bg: "bg-white/[0.04]",
  },
};

const FILLED = 2;
const TOTAL = 9;

export default function EvidenceLedger() {
  return (
    <div className="relative">
      {/* light behind the slab: the only saturated colour in the fold */}
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-1/2 size-[460px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-80 blur-3xl bg-[radial-gradient(circle,color-mix(in_srgb,var(--brand)_26%,transparent),transparent_66%)]"
      />

      {/* The stack: a second sheet behind the ledger. Two sheets read as paper
          on a desk; one sheet reads as a div. */}
      <div className="relative">
        <div
          aria-hidden
          className="absolute inset-0 translate-x-2.5 translate-y-3 rotate-[1.4deg] rounded-[18px] border border-white/10 bg-[var(--ink-800)] shadow-[0_30px_60px_-40px_rgba(8,17,12,0.9)]"
        />

        {/* The sheet is tilted in space and squares up when you point at it. */}
        <div className="relative transition-transform duration-500 ease-out max-lg:[transform:none] lg:[transform:perspective(1400px)_rotateY(-7deg)_rotateX(3.5deg)] lg:hover:[transform:perspective(1400px)_rotateY(-2deg)_rotateX(1deg)] motion-reduce:lg:[transform:none]">
        <div className="sheen relative overflow-hidden rounded-[18px] border border-white/12 bg-[linear-gradient(158deg,var(--ink-800),var(--ink-950)_62%)] shadow-[inset_0_1px_0_rgba(255,255,255,0.09),0_44px_80px_-46px_rgba(8,17,12,0.95)]">
          {/* chrome */}
          <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-2.5">
            <span className="flex items-center gap-2 font-mono type-micro text-[var(--on-ink-dim)]">
              <span aria-hidden className="size-1.5 rounded-full bg-[var(--green-300)]" />
              evidence.ledger
            </span>
            <span className="hidden type-micro text-[var(--on-ink-dim)]/70 sm:inline">
              Northwind Labs · AI Engineer
            </span>
          </div>

          {/* a ghost 09 behind the rows: nine skills, the number the footer
              counts out. Decorative, so it is hidden from the tree. */}
          <span
            aria-hidden
            className="ghost-numeral pointer-events-none absolute -right-1 top-16 select-none text-[120px] text-white/[0.06]"
          >
            09
          </span>

          {/* the ledger's margin rule, like a notebook's */}
          <span
            aria-hidden
            className="pointer-events-none absolute inset-y-0 left-0 w-px bg-[linear-gradient(180deg,transparent,color-mix(in_srgb,var(--green-300)_45%,transparent)_35%,color-mix(in_srgb,var(--green-300)_45%,transparent)_75%,transparent)]"
          />

          {/* the claim column */}
          <div className="px-4 pb-1 pt-4">
            <p className="type-micro m-0 text-[var(--on-ink-dim)]/70">
              What the resume claims
            </p>
          </div>

          <ul className="stagger m-0 list-none p-0">
            {ROWS.map((row) => {
              const stamp = STAMP[row.verdict];
              return (
                <li
                  key={row.claim}
                  className="group flex items-center gap-3 border-t border-white/[0.07] px-4 py-3 transition-colors first:border-t-0 hover:bg-white/[0.03]"
                >
                  <div className="min-w-0 flex-1">
                    <p className="m-0 text-[15px] font-semibold leading-tight text-[var(--on-ink)]">
                      {row.claim}
                    </p>
                    <p className="type-micro m-0 mt-1 text-[var(--on-ink-dim)]/80">
                      {row.level} · {row.note}
                    </p>
                  </div>
                  <span
                    className={`animate-settle shrink-0 rounded-[5px] border px-2 py-[3px] font-mono text-[10px] font-semibold uppercase tracking-[0.1em] ${stamp.text} ${stamp.ring} ${stamp.bg}`}
                    style={{ rotate: row.verdict === "verified" ? "-2deg" : "1.5deg" }}
                  >
                    {row.verdict}
                  </span>
                </li>
              );
            })}
          </ul>

          {/* the total: nine cells, two filled — countable at a glance */}
          <div className="flex items-center gap-3 border-t border-white/10 px-4 py-3.5">
            <div className="flex flex-1 gap-1" aria-hidden>
              {Array.from({ length: TOTAL }, (_, i) => (
                <span
                  key={i}
                  className={`h-1.5 flex-1 rounded-[2px] ${
                    i < FILLED ? "bg-[var(--green-300)]" : "bg-white/12"
                  }`}
                />
              ))}
            </div>
            <p className="m-0 whitespace-nowrap font-mono text-[11px] tabular-nums text-[var(--on-ink-dim)]">
              <span className="text-[var(--on-ink)]">{FILLED}</span> of {TOTAL} proven
            </p>
          </div>
        </div>
      </div>

      </div>

      <p className="type-micro relative m-0 mt-9 flex items-center gap-2 text-[var(--text-dim)]">
        <span aria-hidden className="inline-block h-px w-6 bg-[var(--border-strong)]" />
        Sample sheet · rubric-scored from the transcript alone
      </p>
    </div>
  );
}
