import { cn } from "@/lib/utils";
import IosButton from "@/components/primitives/IosButton";
import { ArrowRight } from "lucide-react";

export default function MarketingFooter() {
  return (
    <footer className="bg-[var(--canvas)] py-12 border-t border-[var(--border)] text-[var(--text-dim)]">
      <div className="max-w-5xl mx-auto px-6 lg:px-12 flex flex-col md:flex-row justify-between items-center gap-6">
        <p className="text-micro uppercase tracking-[0.08em]">© {new Date().getFullYear()} InterviewOS. All rights reserved.</p>
        <div className="flex gap-4">
          <IosButton variant="ghost" size="sm" aria-disabled="true">
            Terms
            <ArrowRight size={12} className="ml-1" aria-hidden />
          </IosButton>
          <IosButton variant="ghost" size="sm" aria-disabled="true">
            Privacy
            <ArrowRight size={12} className="ml-1" aria-hidden />
          </IosButton>
        </div>
      </div>
    </footer>
  );
}
