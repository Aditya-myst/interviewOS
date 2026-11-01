import { cn } from "@/lib/utils";
import IosButton from "@/components/primitives/IosButton";
import { ArrowRight } from "lucide-react";

export default function FinalCTA() {
  return (
    <section className="bg-[var(--accent-soft)] py-24" id="final-cta">
      <div className="max-w-3xl mx-auto px-6 lg:px-12 text-center">
        <p className="text-micro text-[var(--accent-strong)] mb-2 uppercase tracking-[0.08em]">JOIN THE REVOLUTION</p>
        <h2 className="text-display-2 text-[var(--accent-strong)] mb-6">
          Supercharge your interview prep with AI‑driven evidence.
        </h2>
        <IosButton variant="primary" size="lg" arrow>
          Get started now
          <ArrowRight size={16} className="ml-1" />
        </IosButton>
      </div>
    </section>
  );
}
