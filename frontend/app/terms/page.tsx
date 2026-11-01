import type { Metadata } from "next";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import Section from "@/components/marketing/Section";

export const metadata: Metadata = { title: "Terms — InterviewOS" };

const LAST_UPDATED = "1 November 2026";

export default function TermsPage() {
  return (
    <>
      <MarketingNav />
      <Section innerClassName="max-w-[68ch]">
        <p className="type-micro text-[var(--text-dim)] mb-3">Terms</p>
        <h1 className="type-display-2 m-0 mb-3">The short version</h1>
        <p className="type-small text-[var(--text-dim)] mb-10">
          Last updated {LAST_UPDATED}.
        </p>

        <div className="space-y-8">
          <Block title="It is free">
            <li>There is no paid tier, no card, and no trial that expires.</li>
            <li>
              It runs on free model tiers, so during heavy use a request may be
              served by the fallback model or from cache.
            </li>
          </Block>

          <Block title="It is a preparation tool, not a promise">
            <li>
              A readiness score is an estimate of the evidence we have seen. It
              is not a prediction of an interview outcome, and no employment
              result is offered or implied.
            </li>
            <li>
              Never treat generated feedback as authoritative over a real
              interviewer, a textbook or documentation.
            </li>
          </Block>

          <Block title="Upload your own documents">
            <li>
              Only upload a resume you have the right to share. Do not upload
              someone else&apos;s personal data.
            </li>
            <li>
              Do not use the service to generate answers you intend to present as
              your own live interview performance.
            </li>
          </Block>

          <Block title="No warranty">
            <li>
              The software is provided as-is, without warranty of any kind. It is
              an open-source student project, and it may be unavailable while it
              is being deployed.
            </li>
            <li>
              The source is public at{" "}
              <a
                className="text-[var(--brand-strong)] underline underline-offset-4"
                href="https://github.com/Aditya-myst/interviewOS"
                target="_blank"
                rel="noopener noreferrer"
              >
                github.com/Aditya-myst/interviewOS
              </a>
              .
            </li>
          </Block>
        </div>
      </Section>
      <MarketingFooter />
    </>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="type-h4 m-0 mb-2">{title}</h2>
      <ul className="m-0 p-0 list-none space-y-2 type-body text-[var(--text-dim)]">
        {children}
      </ul>
    </section>
  );
}
