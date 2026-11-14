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
        index="02"
        eyebrow="Three steps"
        title="From claim to evidence in one session."
        lead="Most preparation starts with a syllabus. This starts with what the interview will actually ask, and what you can already prove."
      />

      {/* One hairline runs through all three steps on desktop: the steps are a
          sequence, and a row of separate cards hides that. */}
      <div className="relative grid grid-cols-1 gap-8 md:grid-cols-3 md:gap-10">
        <div
          aria-hidden
          className="pointer-events-none absolute left-0 right-0 top-[22px] hidden h-px bg-[linear-gradient(90deg,var(--brand-strong),var(--border-strong)_55%,transparent)] md:block"
        />
        {STEPS.map((s, i) => (
          <Reveal key={s.n} delay={i * 90} className="relative">
            {/* The circle sits on the rail; the title sits below it, so the rule
                never strikes through a word. */}
            <span className="relative z-10 inline-flex size-11 items-center justify-center rounded-full border border-[var(--border-strong)] bg-[var(--canvas)] font-mono text-[13px] font-semibold text-[var(--brand-strong)] shadow-[0_0_0_6px_var(--canvas)]">
              {s.n}
            </span>
            <h3 className="type-h3 mt-5 mb-0">{s.title}</h3>
            <p className="type-small mt-3 mb-0 max-w-[34ch] text-[var(--text-dim)]">{s.body}</p>
            <p className="type-micro m-0 mt-5 flex items-center gap-2 border-t border-[var(--border)] pt-3 text-[var(--text-dim)]">
              <span aria-hidden className="size-1.5 rounded-full bg-[var(--brand)]" />
              {s.note}
            </p>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
