import IosButton from "@/components/primitives/IosButton";
import EvidenceLedger from "./EvidenceLedger";

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
            want, then builds a roadmap from the gaps that will be asked about,
            not the whole syllabus.
          </p>

          <div
            className="animate-rise flex flex-wrap items-center gap-3 mt-8"
            style={{ animationDelay: "330ms" }}
          >
            <IosButton href="/onboarding" variant="primary" size="lg" arrow className="w-full sm:w-auto">
              Start free, upload resume
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

        {/* ── Right: the artifact ─────────────────────────────────────── */}
        <div
          className="animate-rise relative w-full max-w-[420px] mx-auto"
          style={{ animationDelay: "300ms" }}
        >
          <EvidenceLedger />
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
          Scroll: three steps, then the report
        </a>
      </div>
    </section>
  );
}
