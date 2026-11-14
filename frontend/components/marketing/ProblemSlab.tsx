import Section from "./Section";
import Reveal from "./Reveal";
import SectionMarker from "./SectionMarker";

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
    <Section tone="ink" className="relative overflow-hidden bg-[var(--ink-900)] py-20 lg:py-24">
      {/* a whisper of the paper grid, so the ink band is not a flat rectangle */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.14] [background-image:radial-gradient(rgba(231,223,202,0.5)_1px,transparent_1px)] [background-size:22px_22px]"
      />
      <div className="relative">
        <SectionMarker index="01" label="The actual problem" tone="ink" />

        <div className="grid grid-cols-1 gap-px overflow-hidden rounded-[14px] bg-white/12 md:grid-cols-3">
          {ITEMS.map((item, i) => (
            <Reveal key={item.n} delay={i * 90} className="h-full">
              <div className="group h-full bg-[var(--ink-900)] p-6 lg:p-8 transition-colors duration-300 hover:bg-[var(--ink-950)]">
                <span
                  aria-hidden
                  className="ghost-numeral mb-5 block text-[46px] leading-none text-[var(--on-ink)]"
                >
                  {item.n}
                </span>
                <h3 className="type-h3 mb-2 text-[var(--on-ink)]">{item.title}</h3>
                <p className="type-small m-0 text-[var(--on-ink-dim)]">{item.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </Section>
  );
}
