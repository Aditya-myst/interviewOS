import { Check, X } from "lucide-react";
import Section from "./Section";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";

const ROWS = [
  {
    claim: "Knows what you can't do",
    them: "No — it grades the prompt",
    us: "Yes — from your answers",
  },
  {
    claim: "Remembers your progress",
    them: "No — every chat starts fresh",
    us: "Yes — skills stay verified until stale",
  },
  {
    claim: "Learning links",
    them: "Generated, often dead",
    us: "Curated, HTTP-checked, free-first",
  },
  {
    claim: "Explains its priorities",
    them: "Generic advice",
    us: "Every priority cites its evidence",
  },
];

export default function WhyNotChatGPT() {
  return (
    <Section id="why-not-chatgpt">
      <SectionHeading
        eyebrow="Fair question"
        title="Why not just paste it into a chatbot?"
        lead="A chatbot can tell you what a good answer looks like. It cannot tell you whether yours was one — it has no evidence, no memory of your progress, and no reason to keep its links alive."
      />

      <Reveal>
        <div className="card-surface overflow-hidden">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="bg-[var(--surface-2)]">
                <th scope="col" className="type-micro text-[var(--text-dim)] px-5 sm:px-6 py-3">
                  What matters
                </th>
                <th scope="col" className="type-micro text-[var(--text-dim)] px-5 sm:px-6 py-3 hidden sm:table-cell">
                  A generic chatbot
                </th>
                <th scope="col" className="type-micro px-5 sm:px-6 py-3 text-[var(--brand-strong)]">
                  InterviewOS
                </th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((r) => (
                <tr key={r.claim} className="border-t border-[var(--border)] align-top">
                  <th scope="row" className="px-5 sm:px-6 py-4 font-semibold text-left">
                    {r.claim}
                  </th>
                  <td className="px-5 sm:px-6 py-4 hidden sm:table-cell">
                    <span className="flex items-start gap-2 type-small text-[var(--text-dim)]">
                      <X
                        size={16}
                        className="mt-0.5 shrink-0 text-[var(--unverified)]"
                        aria-hidden
                      />
                      {r.them}
                    </span>
                  </td>
                  <td className="px-5 sm:px-6 py-4">
                    <span className="flex items-start gap-2 type-small font-medium">
                      <Check
                        size={16}
                        className="mt-0.5 shrink-0 text-[var(--brand-strong)]"
                        aria-hidden
                      />
                      <span>
                        {r.us}
                        <span className="block sm:hidden text-[var(--text-dim)] font-normal mt-1">
                          vs. {r.them}
                        </span>
                      </span>
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Reveal>
    </Section>
  );
}
