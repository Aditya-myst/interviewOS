import IosButton from "@/components/primitives/IosButton";

export default function FinalCTA() {
  return (
    <section className="bg-[var(--ink-950)] py-28" id="final-cta">
      <div className="max-w-3xl mx-auto px-6 lg:px-12 text-center">
        <p className="text-micro text-[var(--on-ink-dim)] mb-4">
          Ready when you are
        </p>
        <h2 className="text-display-2 text-[var(--on-ink)] mb-5">
          Find out what you actually know.
        </h2>
        <p className="text-body text-[var(--on-ink-dim)] mb-8 max-w-[52ch] mx-auto">
          Four minutes to your first gap report. No card, no signup wall.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <IosButton variant="primary" size="lg" arrow>
            Start free
          </IosButton>
          <IosButton
            variant="ghost"
            size="lg"
            className="text-[var(--on-ink-dim)] hover:text-[var(--on-ink)] hover:bg-[rgba(255,255,255,0.08)]"
          >
            See a sample report
          </IosButton>
        </div>
      </div>
    </section>
  );
}
