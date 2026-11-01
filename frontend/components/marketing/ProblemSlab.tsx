import Section from "./Section";
import Reveal from "./Reveal";

const ITEMS = [
  {
    n: "01",
    title: "Resumes are marketing",
    body: "A listed skill and a demonstrated skill look identical on paper. The interview is where the difference gets discovered.",
  },
  {
    n: "02",
    title: "Generic prep is wasted prep",
    body: "You do not need all of Docker. You need the four Docker questions this role will actually ask.",
  },
  {
    n: "03",
    title: "Advice without evidence",
    body: "Every priority here points back at the answer, project or job line it came from. Nothing is asserted without a citation.",
  },
];

export default function ProblemSlab() {
  return (
    <Section tone="ink" className="bg-[var(--ink-900)] py-20 lg:py-24">
      <p className="type-micro text-[var(--on-ink-dim)] mb-8">The actual problem</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-10">
        {ITEMS.map((item, i) => (
          <Reveal key={item.n} delay={i * 90}>
            <span className="block font-mono text-2xl text-[var(--green-300)] mb-3">
              {item.n}
            </span>
            <h3 className="type-h3 text-[var(--on-ink)] mb-2">{item.title}</h3>
            <p className="type-small text-[var(--on-ink-dim)] m-0">{item.body}</p>
          </Reveal>
        ))}
      </div>
    </Section>
  );
}
