import Section from "./Section";
import Reveal from "./Reveal";
import IosButton from "@/components/primitives/IosButton";

const RECEIPT = ["free", "no card", "~4 minutes", "delete anytime"];

export default function FinalCTA() {
  return (
    <Section tone="ink" className="relative overflow-hidden py-24 lg:py-32">
      {/* Texture instead of a glow: a large green radial over flat ink reads as
          a smudge, whereas the paper grid (borrowed from the closing ink band
          above) reads as the same material the rest of the page is printed on. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.12] [background-image:radial-gradient(rgba(231,223,202,0.5)_1px,transparent_1px)] [background-size:22px_22px]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,transparent,color-mix(in_srgb,var(--brand)_70%,transparent),transparent)]"
      />
      <div className="relative mx-auto max-w-2xl text-center">
        <Reveal>
          <p className="type-micro mb-4 text-[var(--on-ink-dim)]">Ready when you are</p>
          <h2 className="type-display-2 mb-5 text-[var(--on-ink)]">
            Find out what you actually know.
          </h2>
          <p className="type-body mx-auto mb-8 max-w-[52ch] text-[var(--on-ink-dim)]">
            Four minutes to your first gap report. No card, no signup wall.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <IosButton href="/onboarding" variant="primary" size="lg" arrow>
              Start free
            </IosButton>
            <IosButton
              href="#sample-report"
              variant="ghost"
              size="lg"
              className="text-[var(--on-ink-dim)] hover:bg-[rgba(255,255,255,0.08)] hover:text-[var(--on-ink)]"
            >
              See a sample report
            </IosButton>
          </div>

          <ul className="mt-9 flex list-none flex-wrap items-center justify-center gap-x-5 gap-y-2 p-0 font-mono type-micro text-[var(--on-ink-dim)]">
            {RECEIPT.map((item) => (
              <li key={item} className="flex items-center gap-2">
                <span aria-hidden className="size-1 rounded-full bg-[var(--green-300)]" />
                {item}
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </Section>
  );
}
