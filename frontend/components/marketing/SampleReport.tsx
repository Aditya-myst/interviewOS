import IosButton from "@/components/primitives/IosButton";

export default function SampleReport() {
  return (
    <section className="bg-[var(--surface)] py-24" id="sample-report">
      <div className="max-w-5xl mx-auto px-6 lg:px-12 flex flex-col lg:flex-row gap-12 items-center">
        {/* Text side */}
        <div className="flex-1">
          <p className="text-micro text-[var(--text-dim)] mb-2">SAMPLE REPORT</p>
          <h2 className="text-display-2 text-[var(--text)] mb-4">See what your AI‑generated report looks like</h2>
          <p className="text-[var(--text-dim)] mb-6 max-w-[60ch]">
            A concise, evidence‑backed scorecard that tells you exactly where you stand and what to study next.
          </p>
          <IosButton variant="primary" size="lg" arrow>
            Try a demo report
          </IosButton>
        </div>
        {/* Image placeholder */}
        <div className="flex-1 w-full max-w-sm bg-[var(--surface-2)] rounded-[20px] p-4 border border-[var(--border)] shadow-[0_1px_2px_rgba(0,0,0,.06),_0_10px_28px_-14px_rgba(0,0,0,.20)]">
          <div className="w-full h-64 bg-[var(--canvas)] rounded-[12px] flex items-center justify-center text-[var(--text-dim)] text-sm">
            {/* Replace with screenshot when available */}
            Report preview image
          </div>
        </div>
      </div>
    </section>
  );
}
