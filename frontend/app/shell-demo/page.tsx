import type { Metadata } from "next";
import AppShell from "@/components/shell/AppShell";
import PageHeader from "@/components/shell/PageHeader";
import StatRow from "@/components/primitives/StatRow";
import ProgressRow from "@/components/primitives/ProgressRow";
import SkillPill, { type SkillStatus } from "@/components/primitives/SkillPill";
import LegendLadder from "@/components/primitives/LegendLadder";
import BandCard from "@/components/primitives/BandCard";
import IosButton from "@/components/primitives/IosButton";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { AlertTriangle, CheckCircle, Info } from "lucide-react";

export const metadata: Metadata = {
  title: "Shell Demo",
  description: "Visual test page for the InterviewOS design system",
};

/* ─── Section wrapper ─────────────────────────────────────────── */
function Section({
  id,
  title,
  children,
}: {
  id: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} aria-labelledby={`${id}-heading`} className="mb-16">
      <h2
        id={`${id}-heading`}
        className="text-micro text-[var(--text-dim)] mb-4 pb-3 border-b border-[var(--line)]"
      >
        {title}
      </h2>
      {children}
    </section>
  );
}

/* ─── Demo card wrapper ───────────────────────────────────────── */
function DemoCard({
  label,
  children,
  dark = false,
}: {
  label: string;
  children: React.ReactNode;
  dark?: boolean;
}) {
  return (
    <div className="flex flex-col gap-2">
      {/* label is a micro eyebrow — Inter Tight, uppercase, text-dim */}
      <p className="text-micro text-[var(--text-dim)]">{label}</p>
      <div
        className={
          dark
            ? "card-ink p-5 flex flex-wrap items-center gap-3"
            : "card-cream p-5 flex flex-wrap items-center gap-3"
        }
      >
        {children}
      </div>
    </div>
  );
}

/* ─── Banner ──────────────────────────────────────────────────── */
function Banner({
  variant,
  children,
}: {
  variant: "error" | "warning" | "success";
  children: React.ReactNode;
}) {
  const styles = {
    error: {
      bg: "bg-[var(--weak)]/10 border-[var(--weak)]/30",
      text: "text-[var(--weak)]",
      icon: AlertTriangle,
    },
    warning: {
      bg: "bg-[var(--developing)]/10 border-[var(--developing)]/30",
      text: "text-[var(--developing)]",
      icon: AlertTriangle,
    },
    success: {
      bg: "bg-[var(--green-500)]/10 border-[var(--green-700)]/30",
      text: "text-[var(--green-400)]",
      icon: CheckCircle,
    },
  }[variant];

  const Icon = styles.icon;

  return (
    <div
      role="alert"
      className={`flex items-start gap-3 px-4 py-3 rounded-[12px] border ${styles.bg}`}
    >
      <Icon
        size={16}
        className={`${styles.text} shrink-0 mt-0.5`}
        aria-hidden
      />
      <span className={`text-sm ${styles.text}`}>{children}</span>
    </div>
  );
}

/* ─── All six skill statuses ──────────────────────────────────── */
const ALL_STATUSES: { status: SkillStatus; label: string }[] = [
  { status: "weak", label: "System Design" },
  { status: "developing", label: "Behavioral" },
  { status: "verified", label: "DSA — Arrays" },
  { status: "unverified", label: "ML Concepts" },
  { status: "claimed", label: "Distributed Sys." },
  { status: "needs_revision", label: "Concurrency" },
];

/* ─── Page ────────────────────────────────────────────────────── */
export default function ShellDemoPage() {
  return (
    <AppShell targetRole="Senior SWE">
      <div className="max-w-5xl mx-auto">
        {/* 1. Eyebrow corrected: uppercase, exactly "DESIGN SYSTEM / V1" */}
        <PageHeader
          eyebrow="DESIGN SYSTEM / V1"
          title="Shell Demo"
          actions={
            <>
              <IosButton variant="ghost" size="sm">
                Docs
              </IosButton>
              <IosButton variant="primary" size="sm" arrow>
                Start Interview
              </IosButton>
            </>
          }
        />

        {/* ── Banners ───────────────────────────────────────────── */}
        <Section id="banners" title="BANNERS">
          <div className="flex flex-col gap-3">
            <Banner variant="error">
              Something went wrong loading your session data. Refresh to try
              again.
            </Banner>
            <Banner variant="warning">
              Model unavailable — showing deterministic results.
            </Banner>
            <Banner variant="success">
              Interview complete. Your report is ready.
            </Banner>
          </div>
        </Section>

        {/* ── Buttons ───────────────────────────────────────────── */}
        {/* 2. DemoCard labels now use text-micro (Inter Tight, 12px, uppercase, 0.08em) */}
        {/* 4. Primary gallery now shows Small / Medium / Large (lg) + With Arrow */}
        <Section id="buttons" title="BUTTONS">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <DemoCard label="PRIMARY" dark>
              <IosButton variant="primary" size="sm">
                Small
              </IosButton>
              <IosButton variant="primary" size="md">
                Medium
              </IosButton>
              <IosButton variant="primary" size="lg">
                Large
              </IosButton>
              <IosButton variant="primary" size="lg" arrow>
                With Arrow
              </IosButton>
            </DemoCard>

            <DemoCard label="SECONDARY" dark>
              <IosButton variant="secondary" size="sm">
                Small
              </IosButton>
              <IosButton variant="secondary" size="md">
                Medium
              </IosButton>
              <IosButton variant="secondary" size="lg">
                Large
              </IosButton>
            </DemoCard>

            <DemoCard label="GHOST" dark>
              <IosButton variant="ghost" size="sm">
                Small
              </IosButton>
              <IosButton variant="ghost" size="md">
                Medium
              </IosButton>
              <IosButton variant="ghost" size="lg">
                Large
              </IosButton>
            </DemoCard>

            {/* 3. Danger: var(--weak) = #F87171 — confirmed in IosButton variant styles */}
            <DemoCard label="DANGER" dark>
              <IosButton variant="danger" size="sm">
                Delete
              </IosButton>
              <IosButton variant="danger" size="md">
                Remove Session
              </IosButton>
              <IosButton variant="danger" size="lg">
                Permanently Delete
              </IosButton>
            </DemoCard>

            <DemoCard label="STATES" dark>
              <IosButton variant="primary" size="md" disabled>
                Disabled
              </IosButton>
              <IosButton variant="primary" size="md" loading>
                Loading...
              </IosButton>
              <IosButton variant="primary" size="md" arrow>
                Focus Me (Tab)
              </IosButton>
            </DemoCard>
          </div>
        </Section>

        <Separator className="mb-12 bg-[var(--line)]" />

        {/* ── 6. CARDS section ──────────────────────────────────── */}
        <Section id="cards" title="CARDS">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 items-stretch">
            {/* 6a. Cream card */}
            <div
              className="flex flex-col gap-4 p-8 rounded-[20px] text-[var(--text-on-cream)]"
              style={{
                backgroundColor: "var(--cream)",
                boxShadow:
                  "0 1px 2px rgba(0,0,0,.06), 0 10px 28px -14px rgba(0,0,0,.20)",
              }}
            >
              <p className="text-micro text-[var(--text-on-cream)]/50">
                YOUR TOP GAP
              </p>
              <p
                className="text-[var(--text-on-cream)] leading-none tracking-[-0.02em]"
                style={{
                  fontFamily: "var(--font-display)",
                  fontSize: "28px",
                  fontWeight: 900,
                }}
              >
                FastAPI
              </p>
              <SkillPill status="weak" label="Weak" />
              {/* ProgressRow inside cream card — override colours for light bg */}
              <div className="flex flex-col gap-1.5 py-2 border-t border-[var(--text-on-cream)]/10">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-small text-[var(--text-on-cream)]/70 leading-snug">
                    Evidence
                  </span>
                  <span
                    className="text-xs text-[var(--text-on-cream)]/50"
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    1<span className="mx-0.5 opacity-40">/</span>3
                  </span>
                </div>
                <div
                  className="h-[6px] w-full rounded-[999px] overflow-hidden"
                  style={{ background: "rgba(13,26,19,.12)" }}
                  role="progressbar"
                  aria-valuenow={33}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label="Evidence: 1 of 3"
                >
                  <div
                    className="h-full rounded-[999px]"
                    style={{
                      width: "33%",
                      backgroundColor: "var(--weak)",
                    }}
                  />
                </div>
              </div>
              <p className="text-small text-[var(--text-on-cream)]/60 leading-snug">
                You haven't demonstrated FastAPI under timed conditions yet.
                Two more practice sessions will unlock a verified badge.
              </p>
            </div>

            {/* 6b. Ink card */}
            <div
              className="flex flex-col gap-4 p-8 rounded-[20px] border border-[var(--line)]"
              style={{ backgroundColor: "var(--ink-900)" }}
            >
              <p className="text-micro text-[var(--text-dim)]">READINESS</p>
              <p
                className="text-[var(--green-400)] leading-none"
                style={{
                  fontFamily: "var(--font-mono)",
                  fontVariantNumeric: "tabular-nums",
                  fontSize: "48px",
                  fontWeight: 500,
                }}
                aria-label="42 percent readiness"
              >
                42%
              </p>
              <div className="mt-auto">
                <StatRow label="Verified skills" value="2" unit=" / 9" />
                <StatRow label="Mock interviews" value="2" />
              </div>
            </div>
          </div>
        </Section>

        <Separator className="mb-12 bg-[var(--line)]" />

        {/* ── 7. SKILL STATES ────────────────────────────────────── */}
        <Section id="skill-states" title="SKILL STATES">
          <div className="flex flex-col lg:flex-row gap-8 items-start">
            {/* All six pills in a row with status name label */}
            <div className="flex-1 flex flex-col gap-4">
              <p className="text-small text-[var(--text-dim)]">
                All six status variants
              </p>
              <div className="flex flex-wrap gap-3">
                {ALL_STATUSES.map(({ status, label }) => (
                  <div key={status} className="flex flex-col items-start gap-1.5">
                    <SkillPill status={status} label={label} />
                    <span className="text-micro text-[var(--text-dim)] pl-1">
                      {status.replace("_", " ")}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* LegendLadder beside them */}
            <div className="card-ink p-5 shrink-0 min-w-[220px]">
              <p className="text-micro text-[var(--text-dim)] mb-4">LEGEND</p>
              <LegendLadder />
            </div>
          </div>
        </Section>

        <Separator className="mb-12 bg-[var(--line)]" />

        {/* ── 8. STATES ──────────────────────────────────────────── */}
        <Section id="states" title="STATES">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 items-stretch">
            {/* Empty-state cream card */}
            <div
              className="flex flex-col items-center justify-center gap-4 p-8 rounded-[20px] text-center"
              style={{
                backgroundColor: "var(--cream)",
                boxShadow:
                  "0 1px 2px rgba(0,0,0,.06), 0 10px 28px -14px rgba(0,0,0,.20)",
              }}
            >
              <div
                aria-hidden
                className="size-12 rounded-full flex items-center justify-center"
                style={{ background: "rgba(13,26,19,.10)" }}
              >
                <Info
                  size={22}
                  className="text-[var(--text-on-cream)]/50"
                  strokeWidth={1.5}
                />
              </div>
              <div className="space-y-1">
                <p
                  className="text-sm font-semibold"
                  style={{ color: "var(--text-on-cream)" }}
                >
                  No sessions yet
                </p>
                <p
                  className="text-xs leading-snug"
                  style={{ color: "rgba(13,26,19,.55)" }}
                >
                  Complete your first mock interview to see your performance
                  breakdown here.
                </p>
              </div>
              <IosButton variant="primary" size="sm" arrow>
                Start Interview
              </IosButton>
            </div>

            {/* Skeleton blocks — matching a card's height */}
            <div className="card-ink p-5 space-y-3 flex flex-col justify-between min-h-[220px]">
              <div className="space-y-3">
                <Skeleton className="h-3 w-1/3 bg-[var(--ink-700)]" />
                <Skeleton className="h-8 w-2/3 bg-[var(--ink-700)]" />
                <Skeleton className="h-3 w-full bg-[var(--ink-700)]" />
                <Skeleton className="h-3 w-5/6 bg-[var(--ink-700)]" />
              </div>
              <div className="space-y-2">
                <Skeleton className="h-[6px] w-full bg-[var(--ink-700)]" />
                <Skeleton className="h-[6px] w-4/5 bg-[var(--ink-700)]" />
              </div>
            </div>

            {/* Loading spinner button state */}
            <div className="card-ink p-5 flex flex-col items-start justify-between min-h-[220px]">
              <div className="space-y-2">
                <p className="text-micro text-[var(--text-dim)]">LOADING</p>
                <p className="text-small text-[var(--text-dim)]">
                  While data is being fetched, interactive controls enter a
                  loading state.
                </p>
              </div>
              <div className="flex flex-col gap-3 w-full">
                <IosButton variant="primary" size="md" loading className="w-full">
                  Generating report…
                </IosButton>
                <IosButton variant="secondary" size="md" loading className="w-full">
                  Syncing…
                </IosButton>
              </div>
            </div>
          </div>
        </Section>

        <Separator className="mb-12 bg-[var(--line)]" />

        {/* ── Band Cards ────────────────────────────────────────── */}
        <Section id="band-cards" title="BAND CARDS">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <BandCard
              title="System Design"
              count={4}
              band="critical"
              description="Core role requirement"
            />
            <BandCard
              title="Behavioral"
              count={7}
              band="high"
              description="Common in FAANG loops"
            />
            <BandCard
              title="DSA Patterns"
              count={12}
              band="medium"
              description="Partially covered"
            />
            <BandCard
              title="Domain Knowledge"
              count={5}
              band="low"
              description="Lower frequency topics"
            />
          </div>
        </Section>

        <Separator className="mb-12 bg-[var(--line)]" />

        {/* ── Stat Rows ─────────────────────────────────────────── */}
        <Section id="stat-rows" title="STAT ROWS">
          <div className="card-ink p-5 max-w-sm">
            <StatRow label="Overall Score" value="72" unit="/ 100" delta={8} />
            <StatRow label="Sessions Completed" value="14" delta={-2} />
            <StatRow label="Avg. Response Time" value="2m 34s" />
            <StatRow label="Topics Covered" value="38" unit="/ 64" delta={6} />
          </div>
        </Section>

        <Separator className="mb-12 bg-[var(--line)]" />

        {/* ── Progress Rows ─────────────────────────────────────── */}
        <Section id="progress-rows" title="PROGRESS ROWS">
          <div className="card-ink p-5 max-w-sm">
            <ProgressRow title="System Design" current={3} total={10} />
            <ProgressRow title="Behavioral" current={8} total={12} />
            <ProgressRow title="DSA — Arrays" current={15} total={15} />
            <ProgressRow title="Concurrency" current={0} total={8} />
          </div>
        </Section>

        <Separator className="mb-12 bg-[var(--line)]" />

        {/* ── Badges ────────────────────────────────────────────── */}
        <Section id="badges" title="BADGES">
          <div className="flex flex-wrap gap-3">
            <Badge variant="default">Default</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="destructive">Destructive</Badge>
            <Badge variant="outline">Outline</Badge>
            <Badge variant="ghost">Ghost</Badge>
          </div>
        </Section>

        <Separator className="mb-12 bg-[var(--line)]" />

        {/* ── Typography Scale ──────────────────────────────────── */}
        <Section id="typography" title="TYPOGRAPHY SCALE">
          <div className="space-y-4 p-6 card-ink">
            <div>
              <p className="text-micro text-[var(--text-dim)] mb-1">
                DISPLAY-1 / 88PX ARCHIVO BLACK
              </p>
              <p className="text-display-1 text-[var(--text)] leading-none">
                72
              </p>
            </div>
            <div>
              <p className="text-micro text-[var(--text-dim)] mb-1">
                DISPLAY-2 / 56PX ARCHIVO BLACK
              </p>
              <p className="text-display-2 text-[var(--text)] leading-none">
                Senior SWE
              </p>
            </div>
            <div>
              <p className="text-micro text-[var(--text-dim)] mb-1">
                DISPLAY-3 / 40PX ARCHIVO BLACK
              </p>
              <p className="text-display-3 text-[var(--text)] leading-none">
                Gap Analysis
              </p>
            </div>
            <div>
              <p className="text-micro text-[var(--text-dim)] mb-1">
                H3 / 20PX INTER TIGHT
              </p>
              <p className="text-h3 text-[var(--text)]">
                Session breakdown by topic
              </p>
            </div>
            <div>
              <p className="text-micro text-[var(--text-dim)] mb-1">
                BODY / 16PX INTER TIGHT
              </p>
              <p className="text-body text-[var(--text)]">
                Practice targeted questions to build confidence before your
                interview.
              </p>
            </div>
            <div>
              <p className="text-micro text-[var(--text-dim)] mb-1">
                SMALL / 14PX
              </p>
              <p className="text-small text-[var(--text-dim)]">
                Last session: 3 days ago · 45 min
              </p>
            </div>
            <div>
              <p className="text-micro text-[var(--text-dim)] mb-1">
                MICRO / 12PX UPPERCASE INTER TIGHT
              </p>
              <p className="text-micro text-[var(--text-dim)]">
                Section / Label / Eyebrow
              </p>
            </div>
            <div>
              <p className="text-micro text-[var(--text-dim)] mb-1">
                MONO / JETBRAINS MONO TABULAR
              </p>
              <p className="text-mono-value text-[var(--green-400)] text-2xl">
                02:34:07
              </p>
            </div>
          </div>
        </Section>

        <Separator className="mb-12 bg-[var(--line)]" />

        {/* ── Colour Swatches ───────────────────────────────────── */}
        <Section id="colours" title="COLOUR PALETTE">
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {[
              { name: "ink-950", bg: "bg-[var(--ink-950)]", border: true },
              { name: "ink-900", bg: "bg-[var(--ink-900)]", border: true },
              { name: "ink-800", bg: "bg-[var(--ink-800)]", border: true },
              { name: "ink-700", bg: "bg-[var(--ink-700)]", border: true },
              { name: "cream", bg: "bg-[var(--cream)]" },
              { name: "cream-2", bg: "bg-[var(--cream-2)]" },
              { name: "green-400", bg: "bg-[var(--green-400)]" },
              { name: "green-500", bg: "bg-[var(--green-500)]" },
            ].map(({ name, bg, border }) => (
              <div key={name} className="flex flex-col gap-1.5">
                <div
                  className={`h-10 rounded-[12px] ${bg} ${border ? "border border-[var(--line-strong)]" : ""}`}
                />
                <p className="text-micro text-[var(--text-dim)]">{name}</p>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </AppShell>
  );
}
