import IosButton from "@/components/primitives/IosButton";
import SkillPill from "@/components/primitives/SkillPill";

export default function Hero() {
  return (
    <section className="bg-[var(--canvas)] pt-16 pb-20 lg:pt-20 lg:pb-24">
      <div className="max-w-5xl mx-auto px-6 lg:px-12 grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
        {/* ── Left: message ── */}
        <div className="flex flex-col">
          <p className="text-micro text-[var(--text-dim)] mb-5">
            AI career preparation
          </p>

          <h1 className="text-display-1 text-[var(--text)]">
            EVERY RESUME
            <br />
            <span className="text-[var(--brand-strong)]">CLAIMS MORE</span>
            <br />
            THAN IT PROVES.
          </h1>

          <div className="w-16 h-1 bg-[var(--brand)] mt-6 mb-6" aria-hidden />

          <p className="max-w-[46ch] text-body text-[var(--text-dim)]">
            InterviewOS tests what you actually know against the job you actually
            want — then builds a roadmap from the gaps that will be asked about,
            not the whole syllabus.
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-8">
            <IosButton variant="primary" size="lg" arrow>
              Start free — upload resume
            </IosButton>
            <IosButton variant="ghost" size="lg">
              See a sample report
            </IosButton>
          </div>

          <ul className="flex flex-wrap items-center gap-x-3 gap-y-2 mt-7 list-none p-0 text-micro text-[var(--text-dim)]">
            <li className="whitespace-nowrap">No credit card</li>
            <li aria-hidden className="size-[3px] rounded-full bg-[var(--text-dim)]" />
            <li className="whitespace-nowrap">Open-source models</li>
            <li aria-hidden className="size-[3px] rounded-full bg-[var(--text-dim)]" />
            <li className="whitespace-nowrap">Free learning resources only</li>
          </ul>
        </div>

        {/* ── Right: card stack (both cards fully populated) ── */}
        <div className="relative w-full max-w-[380px] mx-auto h-[430px]">
          {/* Back card */}
          <div className="absolute left-4 right-0 top-0 h-[300px] -rotate-2 scale-[0.97] origin-top-left card-inset p-6 flex flex-col items-center justify-center gap-3">
            <p className="text-micro text-[var(--text-dim)]">Readiness</p>
            <p className="font-mono text-[44px] leading-none text-[var(--text)] tabular-nums">
              42%
            </p>
            <div className="w-3/4 h-[6px] rounded-full bg-[var(--surface)] overflow-hidden">
              <div className="h-full bg-[var(--brand)]" style={{ width: "42%" }} />
            </div>
            <p className="text-xs text-[var(--text-dim)] text-center max-w-[24ch]">
              2 of 9 skills verified against the job description
            </p>
          </div>

          {/* Front card */}
          <div className="absolute left-0 right-4 bottom-0 card-surface p-6 hover:-translate-y-0.5 transition-transform duration-150 ease-out">
            <p className="text-micro text-[var(--text-dim)] mb-2">Your top gap</p>
            <h2 className="font-[family-name:var(--font-display)] text-[32px] leading-none text-[var(--text)] mb-3">
              FastAPI
            </h2>

            <div className="flex items-center gap-2 mb-4">
              <SkillPill label="Weak" status="weak" />
            </div>

            <div className="flex items-center justify-between mb-1.5">
              <span className="text-small text-[var(--text-dim)]">Evidence</span>
              <span className="font-mono text-small text-[var(--text-dim)] tabular-nums">
                1 / 3
              </span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-[var(--surface-2)] mb-4 overflow-hidden">
              <div className="h-full bg-[var(--brand)]" style={{ width: "33%" }} />
            </div>

            <blockquote className="text-small italic text-[var(--text-dim)] mb-4">
              “Listed on your resume. Never demonstrated in an assessment.”
            </blockquote>

            <div className="flex items-center justify-between text-small">
              <span className="font-mono text-[var(--text-dim)] tabular-nums">
                PRIORITY 0.52
              </span>
              <span className="bg-[var(--brand-soft)] text-[var(--brand-strong)] px-2 py-1 rounded-[999px] text-xs font-semibold">
                HIGH
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
