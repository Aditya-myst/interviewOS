"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import Section from "./Section";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import IosButton from "@/components/primitives/IosButton";

const FAQS = [
  {
    q: "Is InterviewOS free?",
    a: "Yes. It runs on free model tiers, open-source parsers and free learning resources. There is no paid tier and no card required.",
  },
  {
    q: "Do you store my resume?",
    a: "Yes — privately, inside your own account and protected by row-level security, so your evidence survives between sessions. You can delete your documents at any time.",
  },
  {
    q: "What models power the analysis?",
    a: "Gemini Flash is the primary model, with Groq-hosted open-weight models as a fallback, behind a provider-agnostic gateway. Parsing is deterministic first, so a model outage still produces a full gap analysis.",
  },
  {
    q: "Does it do voice interviews?",
    a: "Yes, push-to-talk with free speech-to-text. Voice is a beta mode, and the report is always generated from the transcript — we never claim to score delivery.",
  },
  {
    q: "How accurate is the assessment?",
    a: "Each skill needs evidence from two to four questions across conceptual, practical and applied levels. Anything you have not proven stays marked unverified instead of guessed.",
  },
];

export default function FAQ() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <Section id="faq" tone="surface">
      <div className="grid grid-cols-1 lg:grid-cols-[0.85fr_1.15fr] gap-10 lg:gap-16">
        <div className="lg:sticky lg:top-24 self-start">
          <SectionHeading
            eyebrow="FAQ"
            title="Common questions"
            lead="Short answers, and the honest limits behind them."
            className="mb-8"
          />
          <IosButton variant="secondary" size="md" arrow>
            Ask something else
          </IosButton>
        </div>

        <div className="border-t border-[var(--border)]">
          {FAQS.map((item, i) => {
            const isOpen = open === i;
            return (
              <Reveal key={item.q} delay={i * 40}>
                <div className="border-b border-[var(--border)]">
                  <h3 className="m-0">
                    <button
                      type="button"
                      onClick={() => setOpen(isOpen ? null : i)}
                      aria-expanded={isOpen}
                      aria-controls={`faq-panel-${i}`}
                      id={`faq-trigger-${i}`}
                      className="w-full flex items-center justify-between gap-4 py-5 text-left type-h4 text-[var(--text)] hover:text-[var(--brand-strong)] transition-colors"
                    >
                      {item.q}
                      <ChevronDown
                        size={18}
                        aria-hidden
                        className={`shrink-0 text-[var(--text-dim)] transition-transform duration-300 ${
                          isOpen ? "rotate-180" : ""
                        }`}
                      />
                    </button>
                  </h3>
                  <div
                    id={`faq-panel-${i}`}
                    role="region"
                    aria-labelledby={`faq-trigger-${i}`}
                    className={`grid transition-all duration-300 ease-out ${
                      isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                    }`}
                  >
                    <div className="overflow-hidden">
                      <p className="type-small text-[var(--text-dim)] m-0 pb-5 max-w-[58ch]">
                        {item.a}
                      </p>
                    </div>
                  </div>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </Section>
  );
}
