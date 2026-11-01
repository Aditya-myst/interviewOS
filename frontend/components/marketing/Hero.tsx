import IosButton from "@/components/primitives/IosButton";

export default function Hero() {
  return (
    <section className="bg-[var(--canvas)] pt-24 min-h-[82vh] flex flex-col lg:flex-row gap-12 max-w-5xl mx-auto px-6 lg:px-12">
      {/* Left column */}
      <div className="flex-1 flex flex-col gap-6">
        <p className="text-micro text-[var(--text-dim)]">AI CAREER PREPARATION</p>
        <h1 className="text-display-1 text-[var(--text)] leading-[0.88] tracking-[-0.03em]">
          EVERY RESUME
          <br />
          <span className="text-[var(--accent-strong)]">CLAIMS MORE</span><br />
          THAN IT PROVES.
        </h1>
        <div className="w-16 h-1 bg-[var(--green-500)] mt-2" />
        <p className="max-w-[46ch] text-body text-[var(--text-dim)]">
          InterviewOS tests what you actually know against the job you actually want — then builds a roadmap from the gaps that will be asked about, not the whole syllabus.
        </p>
        <div className="flex items-center gap-4 mt-4">
          <IosButton variant="primary" size="lg" arrow>
            Start free — upload resume
          </IosButton>
          <IosButton variant="ghost" size="lg" arrow>
            See a sample report
          </IosButton>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-micro text-[var(--text-dim)]" style={{ lineHeight: "1.5" }}>
          <span className="whitespace-nowrap">No credit card</span>
          <span className="inline-block w-3 h-3 bg-[var(--text-dim)] rounded-full" aria-hidden></span>
          <span className="whitespace-nowrap">Open-source models</span>
          <span className="inline-block w-3 h-3 bg-[var(--text-dim)] rounded-full" aria-hidden></span>
          <span className="whitespace-nowrap">Free learning resources only</span>
        </div>
      </div>

      {/* Right column – stacked cards */}
      <div className="relative flex-1 flex items-center justify-center lg:h-auto h-96">
        {/* Back card */}
        <div className="absolute inset-0 w-[90%] max-w-sm transform -rotate-2 scale-[0.96] bg-[var(--surface-2)] rounded-[20px] p-5 border border-[var(--border)] shadow-none flex flex-col gap-2 justify-center items-center">
          <p className="text-micro text-[var(--text-dim)] uppercase tracking-[0.08em]">READINESS</p>
          <p className="font-mono text-[40px] text-[var(--text)]">42%</p>
          <div className="w-3/4 h-[6px] bg-[var(--surface)] rounded-full overflow-hidden">
            <div className="h-full bg-[var(--accent)]" style={{ width: "42%" }}></div>
          </div>
        </div>
        {/* Front card */}
        <div className="relative w-[90%] max-w-sm bg-[var(--surface)] rounded-[20px] p-5 border border-[var(--border)] shadow-[0_1px_2px_rgba(0,0,0,.06),_0_10px_28px_-14px_rgba(0,0,0,.20)] hover:transform hover:-translate-y-0.5 transition-transform duration-150 ease-out">
          <p className="text-micro text-[var(--text-dim)] mb-2">YOUR TOP GAP</p>
          <h2 className="text-[32px] font-display font-black text-[var(--text)] leading-none mb-2">FastAPI</h2>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-block bg-[var(--weak)] text-[var(--weak)] px-2 py-0.5 rounded-full text-xs" style={{ paddingLeft: "0.5rem", paddingRight: "0.5rem" }}>Weak</span>
          </div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-[var(--text-dim)]">Evidence</span>
            <span className="font-mono text-[var(--text-dim)]">1 / 3</span>
          </div>
          <div className="h-1.5 w-full bg-[var(--surface)] rounded-full mb-3" aria-label="Evidence progress 42%">
            <div className="h-full bg-[var(--accent)]" style={{ width: "42%" }}></div>
          </div>
          <blockquote className="text-sm text-[var(--text-dim)] italic mb-3">
            “Listed on your resume. Never demonstrated in an assessment.”
          </blockquote>
          <div className="flex items-center justify-between text-sm">
            <span className="font-mono text-[var(--text-dim)]">PRIORITY 0.52</span>
            <span className="bg-[var(--accent-soft)] text-[var(--accent-strong)] px-2 py-0.5 rounded-full">HIGH</span>
          </div>
        </div>
      </div>
    </section>
  );
}
