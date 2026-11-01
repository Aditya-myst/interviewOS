"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import IosButton from "@/components/primitives/IosButton";

const LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#sample-report", label: "Sample report" },
  { href: "#faq", label: "FAQ" },
];

export default function MarketingNav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={`sticky top-0 z-40 bg-[var(--canvas)]/92 backdrop-blur-md border-b transition-[border-color,box-shadow] duration-200 ${
        scrolled
          ? "border-[var(--border)] shadow-[0_1px_0_rgba(13,26,19,0.04)]"
          : "border-transparent"
      }`}
    >
      <div className="max-w-6xl mx-auto h-[72px] px-6 lg:px-10 flex items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-1.5 shrink-0">
          <span className="font-[family-name:var(--font-display)] text-[20px] text-[var(--text)] tracking-[-0.02em]">
            InterviewOS
          </span>
          <span className="inline-block size-2 rounded-[2px] bg-[var(--brand)]" aria-hidden />
        </Link>

        <nav aria-label="Sections" className="hidden md:flex items-center gap-8 text-sm">
          {LINKS.map(({ href, label }) => (
            <a
              key={href}
              href={href}
              className="relative py-1 text-[var(--text-dim)] hover:text-[var(--text)] transition-colors after:absolute after:left-0 after:-bottom-0.5 after:h-[2px] after:w-0 after:bg-[var(--brand)] after:transition-all after:duration-200 hover:after:w-full focus-visible:after:w-full"
            >
              {label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <IosButton
            href="/onboarding"
            variant="primary"
            size="sm"
            arrow
            aria-label="Start free — upload your resume"
          >
            Start free
          </IosButton>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label={open ? "Close menu" : "Open menu"}
            className="md:hidden inline-flex items-center justify-center size-11 rounded-[12px] text-[var(--text)] hover:bg-[rgba(13,26,19,0.06)]"
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <div
        id="mobile-menu"
        className={`md:hidden absolute left-0 right-0 top-full overflow-hidden border-t border-[var(--border)] bg-[var(--canvas)] shadow-[0_18px_40px_-24px_rgba(13,26,19,0.35)] transition-[max-height,opacity] duration-300 ease-out ${
          open ? "max-h-[340px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <nav aria-label="Mobile sections" className="px-6 py-4 flex flex-col">
          {LINKS.map(({ href, label }) => (
            <a
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className="py-3 text-[17px] text-[var(--text)] border-b border-[var(--border)] last:border-0"
            >
              {label}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}
