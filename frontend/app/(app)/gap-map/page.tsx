import Link from "next/link";
import { ArrowRight } from "lucide-react";
import PageHeader from "@/components/shell/PageHeader";
import IosButton from "@/components/primitives/IosButton";
import GapMapTable from "@/components/app/GapMapTable";
import StateNotice from "@/components/app/StateNotice";
import { skillProfileFixture } from "@/lib/fixtures";

export const metadata = { title: "Gap map — InterviewOS" };

export default function GapMapPage() {
  const p = skillProfileFixture;

  return (
    <div className="max-w-[1180px] mx-auto">
      <PageHeader
        eyebrow={`${p.skills.length} skills · ${p.counts.verified} verified`}
        title="Every skill, and the evidence behind it"
        actions={
          <IosButton href="/roadmap" variant="primary" size="md" arrow>
            Open roadmap
          </IosButton>
        }
      />

      {p.provisional && (
        <div className="mb-5">
          <StateNotice title="This map is provisional">
            {p.counts.critical} critical and {p.counts.high} high-band skills
            still need assessment evidence. Bands are recomputed on every answer,
            so nothing here is frozen.
          </StateNotice>
        </div>
      )}

      <GapMapTable skills={p.skills} />

      <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 type-small text-[var(--text-dim)]">
        <span>
          Priority = JD importance × gap × interview relevance. Bands: ≥0.55
          critical, ≥0.35 high, ≥0.18 medium, else low.
        </span>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 font-medium text-[var(--brand-strong)] hover:underline underline-offset-4"
        >
          Back to dashboard
          <ArrowRight size={14} aria-hidden />
        </Link>
      </div>
    </div>
  );
}
