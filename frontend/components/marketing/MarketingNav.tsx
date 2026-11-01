import Link from "next/link";
import IosButton from "@/components/primitives/IosButton";

const LINKS = [
  { href: "/#how-it-works", label: "How it works" },
  { href: "/#sample-report", label: "Sample report" },
  { href: "/#faq", label: "FAQ" },
];

export default function MarketingNav() {
  return (
    <header className="sticky top-0 z-30 h-[72px] flex items-center justify-between px-6 lg:px-12 bg-[var(--canvas)]/92 backdrop-blur-md border-b border-[var(--border)]">
      <Link href="/" className="flex items-center gap-1.5 shrink-0">
        <span className="font-[family-name:var(--font-display)] text-[20px] text-[var(--text)] tracking-[-0.02em]">
          InterviewOS
        </span>
        <span
          className="inline-block size-2 rounded-[2px] bg-[var(--brand)]"
          aria-hidden
        />
      </Link>

      <nav
        aria-label="Sections"
        className="hidden md:flex items-center gap-8 text-sm"
      >
        {LINKS.map(({ href, label }) => (
          <a
            key={href}
            href={href}
            className="relative py-1 text-[var(--text-dim)] hover:text-[var(--text)] transition-colors after:absolute after:left-0 after:-bottom-0.5 after:h-[2px] after:w-0 after:bg-[var(--brand)] after:transition-all after:duration-150 hover:after:w-full focus-visible:after:w-full"
          >
            {label}
          </a>
        ))}
      </nav>

      <div className="flex items-center gap-2">
        <Link
          href="/login"
          className="hidden sm:inline-flex items-center h-10 px-3 text-sm font-medium text-[var(--text-dim)] hover:text-[var(--text)] rounded-[12px]"
        >
          Sign in
        </Link>
        <Link href="/onboarding" aria-label="Start free — upload your resume">
          <IosButton variant="primary" size="sm" arrow tabIndex={-1}>
            Start free
          </IosButton>
        </Link>
      </div>
    </header>
  );
}
