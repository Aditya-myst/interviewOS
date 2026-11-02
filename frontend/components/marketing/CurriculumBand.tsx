import Section from "./Section";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import SkillHelix from "./SkillHelix";
import { getTaxonomy } from "@/lib/taxonomy";

/**
 * The curriculum, as data rather than adjectives.
 *
 * Every number here is read from contracts/taxonomy.json, which is generated from the
 * same taxonomy.yaml and curated.yaml the product runs on — so this section cannot
 * brag about a catalogue that does not exist. The right-hand column states the gap in
 * the same breath: 22 of 41 skills have no curated resource yet, and the roadmap says
 * so instead of filling the hole.
 */
export default function CurriculumBand() {
  const { totals, skills, updated } = getTaxonomy();
  const withResources = skills.filter((s) => s.resources > 0);
  const gapSkills = totals.skills - totals.skills_with_resources;
  // Every skill that has at least one curated resource: 19 chips over two turns of
  // the coil. The 22 with none would be chips reading "—", which is an honest number
  // in the paragraph but a hole in the visual.
  const helix = withResources.slice(0, 12);

  return (
    <Section id="curriculum">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_0.85fr] gap-10 lg:gap-14 items-center">
        <div>
          <SectionHeading
            eyebrow="The curriculum"
            title={
              <>
                {totals.skills} skills. {totals.subtopics} subtopics.
                <br />
                <span className="text-[var(--brand-strong)]">
                  {totals.resources} links, each one checked.
                </span>
              </>
            }
            lead="The graph is hand-curated per role, not scraped: every skill breaks into
            concrete subtopics with an objective, and every resource is fetched over
            HTTP before it is shown — no login walls, no dead links, no search results."
          />

          <Reveal delay={120}>
            <dl className="grid grid-cols-3 gap-4 mt-8 max-w-[520px]">
              {[
                ["Skills", totals.skills],
                ["With resources", totals.skills_with_resources],
                ["Links verified", totals.resources],
              ].map(([label, value]) => (
                <div key={String(label)}>
                  <dt className="type-micro text-[var(--text-dim)] m-0">{label}</dt>
                  <dd className="font-mono tabular-nums text-[26px] leading-none text-[var(--text)] m-0 mt-1.5">
                    {value}
                  </dd>
                </div>
              ))}
            </dl>
          </Reveal>

          <Reveal delay={200}>
            <p className="mt-6 max-w-[52ch] type-small text-[var(--text-dim)]">
              {gapSkills} of {totals.skills} skills still have no curated resource.
              They appear in a roadmap as named gaps — “no checkpoint yet” — rather
              than as a generated link that might not exist.
              {updated ? ` Catalogue checked ${updated}.` : ""}
            </p>
          </Reveal>
        </div>

        <Reveal delay={80} className="min-w-0">
          {/* Below 1024px the coil cannot be shown at a legible size, so it is not
              shrunk into illegibility — the same twelve skills are listed instead. */}
          <div className="hidden lg:block">
            <SkillHelix items={helix} />
            <p className="mt-2 text-center type-micro text-[var(--text-dim)]">
              Point at the helix to hold it still. The number is curated resources
              behind that skill.
            </p>
          </div>

          <div className="lg:hidden">
            <p className="type-micro text-[var(--text-dim)] mb-3">
              Most-covered skills · curated resources
            </p>
            <ul className="grid grid-cols-2 gap-x-6 gap-y-0 list-none p-0 m-0">
              {helix.map((s) => (
                <li
                  key={s.id}
                  className="flex items-baseline gap-2 border-b border-[var(--border)] py-2"
                >
                  <span className="type-small text-[var(--text)] truncate">{s.name}</span>
                  <span className="ml-auto font-mono type-micro tabular-nums text-[var(--text-dim)]">
                    {s.resources}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </Reveal>
      </div>
    </Section>
  );
}
