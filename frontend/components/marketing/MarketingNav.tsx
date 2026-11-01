"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import IosButton from "@/components/primitives/IosButton";
import { ArrowRight } from "lucide-react";

export default function MarketingNav() {
  const pathname = usePathname();
  const linkClasses = (active: boolean) =>
    cn(
      "text-[var(--text-dim)] hover:text-[var(--text)] transition-colors",
      active && "text-[var(--text)]"
    );

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-18 bg-[var(--canvas)] border-b border-[var(--border)] px-6 lg:px-12">
      {/* Wordmark */}
      <div className="flex items-center gap-1">
        <span className="font-display text-[20px] text-[var(--text)] tracking-tight">
          InterviewOS
        </span>
        <span className="inline-block w-2 h-2 bg-[var(--green-500)] rounded-sm" aria-hidden />
      </div>

      {/* Center links */}
      <nav className="hidden md:flex gap-8 text-sm">
        <Link href="#how-it-works" className={linkClasses(pathname.startsWith("/how-it-works"))}>
          How it works
        </Link>
        <Link href="#sample-report" className={linkClasses(pathname.startsWith("/sample-report"))}>
          Sample report
        </Link>
        <Link href="#faq" className={linkClasses(pathname.startsWith("/faq"))}>
          FAQ
        </Link>
      </nav>

      {/* Right actions */}
      <div className="flex items-center gap-3">
        <IosButton variant="ghost" size="sm" aria-disabled="true">
          Sign in
        </IosButton>
        <IosButton variant="primary" size="sm" arrow aria-disabled="true">
          Start free
        </IosButton>
      </div>
    </header>
  );
}
