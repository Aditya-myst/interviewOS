import Section from "./Section";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";

const STEPS = [
  {
    n: "01",
    title: "Claim",
    body: "Upload your resume and paste the job description you are actually targeting.",
    note: "PDF or DOCX — never stored publicly",
  },
  {
    n: "02",
    title: "Verify",
    body: "Short adaptive checks across three levels: conceptual, practical, applied.",
    note: "2–4 questions per skill, rubric-scored",
  },
  {
    n: "03",
    title: "Close the gap",
    body: "A roadmap ordered by interview impact, with verified free resources only.",
    note: "Docs, not dead links — every URL checked",
  },
];

export default function HowItWorks() {
  return (
    <Section id="how-it-works">
      <SectionHeading
        eyebrow="Three steps"
        title="From claim to evidence in one session."
        lead="Most preparation starts with a syllabus. This starts with what the interview will actually ask, and what you can already prove."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 lg:gap-6">
        {STEPS.map((s, i) => (
          <Reveal key={s.n} delay={i * 90}>
            <div className="card-surface p-6 h-full transition-transform duration-200 hover:-translate-y-1">
              <span className="inline-flex items-center justify-center size-9 rounded-full bg-[var(--brand-soft)] text-[var(--brand-strong)] font-mono text-xs font-semibold">
                {s.n}
              </span>
              <h3 className="type-h3 mt-4 mb-2">{s.title}</h3>
              <p className="type-small text-[var(--text-dim)] mb-4">{s.body}</p>
              <p className="type-micro text-[var(--text-dim)] m-0 pt-3 border-t border-[var(--border)]">
                {s.note}
              </p>
            </div>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
