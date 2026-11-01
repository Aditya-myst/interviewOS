import IosButton from "@/components/primitives/IosButton";

/**
 * Copy rule: every answer here must be literally true of the product.
 * No "we never store your resume" (we do, privately), no pricing tiers
 * that do not exist, no model names we do not run.
 */
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
  return (
    <section className="bg-[var(--canvas)] py-24" id="faq">
      <div className="max-w-3xl mx-auto px-6 lg:px-12">
        <p className="text-micro text-[var(--text-dim)] mb-4">FAQ</p>
        <h2 className="text-display-2 text-[var(--text)] mb-10">
          Common questions
        </h2>

        <dl className="m-0">
          {FAQS.map(({ q, a }) => (
            <div
              key={q}
              className="border-t border-[var(--border)] py-6 last:border-b"
            >
              <dt className="text-h3 text-[var(--text)] mb-2">{q}</dt>
              <dd className="text-small text-[var(--text-dim)] m-0 max-w-[62ch]">
                {a}
              </dd>
            </div>
          ))}
        </dl>

        <div className="mt-10">
          <IosButton variant="secondary" size="md" arrow>
            Ask something else
          </IosButton>
        </div>
      </div>
    </section>
  );
}
