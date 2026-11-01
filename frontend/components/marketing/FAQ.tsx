import { cn } from "@/lib/utils";
import IosButton from "@/components/primitives/IosButton";
import { ArrowRight } from "lucide-react";

export default function FAQ() {
  const faqs = [
    {
      q: "Is InterviewOS really free?",
      a: "Yes – all core features are free. We only charge for premium mentorship services, which are optional.",
    },
    {
      q: "Do you store my resume?",
      a: "We never store your resume. It’s processed in‑memory and deleted immediately after generating the report.",
    },
    {
      q: "What models power the analysis?",
      a: "Open‑source Llama‑3.1 and Gemini models run on our secure backend, no proprietary API keys needed.",
    },
  ];
  return (
    <section className="bg-[var(--canvas)] py-24" id="faq">
      <div className="max-w-5xl mx-auto px-6 lg:px-12">
        <p className="text-micro text-[var(--text-dim)] mb-4">FAQ</p>
        <h2 className="text-display-2 text-[var(--text)] mb-8">Common questions</h2>
        <dl className="space-y-6">
          {faqs.map(({ q, a }) => (
            <div key={q} className="border-b border-[var(--border)] pb-4">
              <dt className="font-semibold text-[var(--text)] mb-2">{q}</dt>
              <dd className="text-[var(--text-dim)]">{a}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-8 text-center">
          <IosButton variant="primary" size="lg">
            Still have questions?
            <ArrowRight size={14} className="ml-1" />
          </IosButton>
        </div>
      </div>
    </section>
  );
}
