import Section from "./Section";
import Reveal from "./Reveal";
import IosButton from "@/components/primitives/IosButton";

export default function FinalCTA() {
  return (
    <Section tone="ink" className="py-24 lg:py-32 text-center">
      <Reveal>
        <p className="type-micro text-[var(--on-ink-dim)] mb-4">Ready when you are</p>
        <h2 className="type-display-2 text-[var(--on-ink)] mb-5">
          Find out what you actually know.
        </h2>
        <p className="type-body text-[var(--on-ink-dim)] mb-8 max-w-[52ch] mx-auto">
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
            className="text-[var(--on-ink-dim)] hover:text-[var(--on-ink)] hover:bg-[rgba(255,255,255,0.08)]"
          >
            See a sample report
          </IosButton>
        </div>
      </Reveal>
    </Section>
  );
}
