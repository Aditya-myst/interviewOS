import IosButton from "@/components/primitives/IosButton";
import SkillPill from "@/components/primitives/SkillPill";
import CountUp from "./CountUp";

/* Every figure here is one the product can back up: the four-minute figure is
   the FAQ's, the nine skills are the fixture JD's, the zero is the pricing. */
const PROOF = [
  { k: "~4 min", v: "to a first gap report" },
  { k: "9", v: "skills matched to this job" },
  { k: "₹0", v: "no card, no signup wall" },
];

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-[var(--canvas)] pt-14 pb-16 lg:pt-20 lg:pb-20">
      <div className="max-w-6xl mx-auto px-6 lg:px-10 grid grid-cols-1 lg:grid-cols-[1.08fr_0.92fr] gap-12 lg:gap-16 items-center">
        {/* ── Left: the claim ─────────────────────────────────────────── */}
        <div className="flex flex-col">
          <p
            className="animate-rise type-micro flex items-center gap-2.5 text-[var(--text-dim)] mb-6"
            style={{ animationDelay: "40ms" }}
          >
            <span aria-hidden className="inline-block h-px w-8 bg-[var(--brand-strong)]" />
            AI career preparation
          </p>

          {/* Three lines, three delays: the headline arrives like a stamp
              hitting paper three times rather than as one block. */}
          <h1 className="type-hero text-[var(--text)] m-0">
            <span className="animate-rise block" style={{ animationDelay: "90ms" }}>
              EVERY RESUME
            </span>
            <span
              className="animate-rise block text-[var(--brand-strong)]"
              style={{ animationDelay: "150ms" }}
            >
              CLAIMS MORE
            </span>
            <span className="animate-rise block" style={{ animationDelay: "210ms" }}>
              THAN IT PROVES.
            </span>
          </h1>

          <p
            className="animate-rise max-w-[46ch] type-body text-[var(--text-dim)] mt-6"
            style={{ animationDelay: "270ms" }}
          >
            InterviewOS tests what you actually know against the job you actually
            want — then builds a roadmap from the gaps that will be asked about,
            not the whole syllabus.
          </p>

          <div
            className="animate-rise flex flex-wrap items-center gap-3 mt-8"
            style={{ animationDelay: "330ms" }}
          >
            <IosButton href="/onboarding" variant="primary" size="lg" arrow className="w-full sm:w-auto">
              Start free — upload resume
            </IosButton>
            <IosButton href="#sample-report" variant="secondary" size="lg" className="w-full sm:w-auto">
              See a sample report
            </IosButton>
          </div>

          <dl
            /* On a phone three columns of micro-labels wrap to four lines each, so
               the strip becomes three rows with the figure leading. */
            className="animate-rise mt-10 mb-0 grid grid-cols-1 gap-px overflow-hidden rounded-[14px] border border-[var(--border)] bg-[var(--border)] sm:grid-cols-3"
            style={{ animationDelay: "390ms" }}
          >
            {PROOF.map((item) => (
              <div
                key={item.k}
                className="flex items-baseline justify-between gap-3 bg-[var(--canvas)] px-4 py-3 sm:block"
              >
                <dt className="font-mono text-[17px] leading-none text-[var(--text)] tabular-nums">
                  {item.k}
                </dt>
                <dd className="type-micro text-[var(--text-dim)] m-0 leading-snug sm:mt-2">
                  {item.v}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        {/* ── Right: a real product surface, framed as an artifact ────── */}
        <div
          className="animate-rise relative w-full max-w-[420px] mx-auto"
          style={{ animationDelay: "300ms" }}
        >
          {/* the one piece of free colour on the page */}
          <div
            aria-hidden
            className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 size-[440px] rounded-full opacity-70 blur-3xl bg-[radial-gradient(circle,color-mix(in_srgb,var(--brand)_22%,transparent),transparent_68%)]"
          />

          <figure className="relative m-0 overflow-hidden rounded-[16px] border border-[var(--border-strong)] bg-[var(--surface)] shadow-[0_30px_60px_-40px_rgba(13,26,19,0.55)]">
            {/* window chrome — this is a report, and it says which one */}
            <div className="flex items-center justify-between gap-3 border-b border-[var(--border)] bg-[var(--surface-2)] px-4 py-2.5">
              <span className="type-micro font-mono text-[var(--text-dim)]">
                report.preflight
              </span>
              <span className="type-micro text-[var(--text-dim)]">
                Northwind Labs · AI Engineer
              </span>
            </div>

            {/* the two cards */}
            <div className="relative h-[452px] px-5 pt-5">
              <div className="absolute inset-x-9 top-5 h-[206px] -rotate-2 rounded-[14px] border border-[var(--border)] bg-[var(--surface-2)] px-6 pt-6 flex flex-col items-center gap-3 shadow-[0_18px_40px_-28px_rgba(13,26,19,0.45)]">
                <p className="type-micro text-[var(--text-dim)] m-0">Readiness</p>
                <p className="font-mono text-[40px] leading-none text-[var(--text)] tabular-nums m-0">
                  <CountUp to={42} suffix="%" />
                </p>
                <p className="type-micro m-0 mt-1 text-[var(--text-dim)]">2 of 9 verified</p>
                <div className="mt-1 w-3/4 h-[6px] overflow-hidden rounded-full bg-[var(--canvas)]">
                  <div className="h-full bg-[var(--brand)]" style={{ width: "42%" }} />
                </div>
              </div>

              <div className="card-lift absolute inset-x-0 bottom-0 rounded-[14px] border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[0_22px_44px_-30px_rgba(13,26,19,0.5)]">
                <p className="type-micro text-[var(--text-dim)] m-0 mb-2">Your top gap</p>
                <h2 className="m-0 mb-3 font-[family-name:var(--font-display)] text-[30px] leading-none text-[var(--text)]">
                  FastAPI
                </h2>

                <div className="mb-4 flex items-center gap-2">
                  <SkillPill label="Weak" status="weak" />
                </div>

                <div className="mb-1.5 flex items-center justify-between">
                  <span className="type-small text-[var(--text-dim)]">Evidence</span>
                  <span className="type-small font-mono tabular-nums text-[var(--text-dim)]">
                    1 / 3
                  </span>
                </div>
                <div className="mb-4 h-1.5 w-full overflow-hidden rounded-full bg-[var(--surface-2)]">
                  <div className="h-full bg-[var(--brand)]" style={{ width: "33%" }} />
                </div>

                <blockquote className="m-0 mb-4 type-small italic text-[var(--text-dim)]">
                  “Listed on your resume. Never demonstrated in an assessment.”
                </blockquote>

                <div className="flex items-center justify-between type-small">
                  <span className="font-mono tabular-nums text-[var(--text-dim)]">
                    PRIORITY 0.52
                  </span>
                  <span className="rounded-[999px] bg-[var(--brand-soft)] px-2 py-1 text-xs font-semibold text-[var(--brand-strong)]">
                    HIGH
                  </span>
                </div>
              </div>
            </div>

            {/* the receipt line: what the frame above adds up to */}
            <figcaption className="flex items-center justify-between gap-3 border-t border-[var(--border)] px-4 py-2.5 font-mono type-micro text-[var(--text-dim)] tabular-nums">
              <span>9 claims</span>
              <span className="text-[var(--brand-strong)]">2 verified</span>
              <span>7 open</span>
            </figcaption>
          </figure>
        </div>
      </div>

      {/* scroll cue */}
      <div className="mx-auto mt-14 hidden max-w-6xl px-6 lg:block lg:px-10">
        <a
          href="#how-it-works"
          className="group inline-flex items-center gap-2 type-micro text-[var(--text-dim)] no-underline hover:text-[var(--text)]"
        >
          <span className="cue-bob inline-block" aria-hidden>
            ↓
          </span>
          Scroll — three steps, then the report
        </a>
      </div>
    </section>
  );
}
