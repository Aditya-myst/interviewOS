import type { Metadata } from "next";
import MarketingNav from "@/components/marketing/MarketingNav";
import MarketingFooter from "@/components/marketing/MarketingFooter";
import Section from "@/components/marketing/Section";

export const metadata: Metadata = { title: "Privacy — InterviewOS" };

const LAST_UPDATED = "1 November 2026";

export default function PrivacyPage() {
  return (
    <>
      <MarketingNav />
      <Section innerClassName="max-w-[68ch]">
        <p className="type-micro text-[var(--text-dim)] mb-3">Privacy</p>
        <h1 className="type-display-2 m-0 mb-3">What we store, and where</h1>
        <p className="type-small text-[var(--text-dim)] mb-10">
          Last updated {LAST_UPDATED}. This page describes what the code in this
          repository actually does — not what a template says.
        </p>

        <div className="space-y-8">
          <Block title="What we keep">
            <li>Your resume file, and the text extracted from it.</li>
            <li>
              The exact sentences we quote as evidence, with their position in
              the source document.
            </li>
            <li>
              The job description you paste, and the requirements we parse from
              it.
            </li>
            <li>
              Your assessment answers, mock-interview transcripts, and the skill
              statuses derived from them.
            </li>
          </Block>

          <Block title="Where it lives">
            <li>
              Resume files go to a private storage bucket with one folder per
              account; the file is never publicly readable.
            </li>
            <li>
              Everything else is in Postgres, with row-level security enabled on
              every user-facing table: a query made with your session can only
              return rows whose <code>user_id</code> is yours.
            </li>
            <li>
              The service key that can bypass those rules exists only on the
              server and is never sent to the browser.
            </li>
          </Block>

          <Block title="Third parties">
            <li>
              Resume and job-description text is sent to Gemini Flash, or to
              Groq-hosted open-weight models as a fallback, for parsing and
              question generation. Nothing is sent to any other provider from the
              conversion path.
            </li>
            <li>
              Model responses are cached by a hash of the prompt so a repeated
              request does not spend quota — the cache is service-role only.
            </li>
            <li>
              We do not sell data, run ads, or ship third-party analytics or
              session recording.
            </li>
          </Block>

          <Block title="Deleting it">
            <li>
              Deleting a resume removes its extracted text and the evidence
              quotes drawn from it.
            </li>
            <li>
              Deleting your account removes your profile, documents, skills,
              assessments, paths, interviews and reports — by database cascade,
              not by a cleanup script that might be forgotten.
            </li>
          </Block>

          <Block title="Questions">
            <li>
              Open an issue at{" "}
              <a
                className="text-[var(--brand-strong)] underline underline-offset-4"
                href="https://github.com/Aditya-myst/interviewOS/issues"
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
