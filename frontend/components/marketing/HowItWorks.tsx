import { cn } from "@/lib/utils";
import IosButton from "@/components/primitives/IosButton";
import { ArrowRight } from "lucide-react";

export default function HowItWorks() {
  const steps = [
    {
      number: "01",
      title: "Claim",
      body: "Upload your resume and paste the job description.",
      footnote: "PDF or DOCX, never stored publicly",
    },
    {
      number: "02",
      title: "Verify",
      body: "Short adaptive checks across three levels: conceptual, practical, applied.",
      footnote: "2–4 questions per skill, rubric‑scored",
    },
    {
      number: "03",
      title: "Close the gap",
      body: "A roadmap ordered by interview impact, with verified free resources only.",
      footnote: "Docs, not dead links — every URL checked",
    },
  ];
  return (
    <section className="bg-[var(--canvas)] py-24" id="how-it-works">
      <div className="max-w-5xl mx-auto px-6 lg:px-12">
        <p className="text-micro text-[var(--text-dim)] mb-4">THREE STEPS</p>
        <h2 className="text-display-2 text-[var(--text)] mb-8">
          From claim to evidence in one session.
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map(({ number, title, body, footnote }) => (
            <div
              key={number}
              className="card-cream p-5 border border-[var(--border)] rounded-[20px] hover:transform hover:-translate-y-0.5 transition-transform duration-150 ease-out"
            >
              <span className="text-[var(--green-700)] font-mono text-2xl mb-2 block">{number}</span>
              <h3 className="text-lg font-semibold mb-2 text-[var(--text)]">{title}</h3>
              <p className="text-sm text-[var(--text-dim)] mb-3">{body}</p>
              <p className="text-micro text-[var(--text-dim)]">{footnote}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
