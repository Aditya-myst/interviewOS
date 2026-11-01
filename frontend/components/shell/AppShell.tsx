"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Map,
  Route,
  GraduationCap,
  Mic2,
  FileText,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/* ─── Nav items ──────────────────────────────────────────────── */
const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/gap-map", label: "Gap Map", icon: Map },
  { href: "/roadmap", label: "Roadmap", icon: Route },
  { href: "/tutor", label: "Tutor", icon: GraduationCap },
  { href: "/interview", label: "Interview", icon: Mic2 },
  { href: "/report", label: "Report", icon: FileText },
] as const;

/* ─── NavLink ─────────────────────────────────────────────────── */
function NavLink({
  item,
  iconOnly,
  onClick,
}: {
  item: (typeof NAV_ITEMS)[number];
  iconOnly: boolean;
  onClick?: () => void;
}) {
  const pathname = usePathname();
  // Dashboard is also active on /shell-demo (design system demo route)
  const active =
    pathname === item.href || pathname.startsWith(item.href + "/");
  const Icon = item.icon;

  const content = (
    <Link
      href={item.href}
      onClick={onClick}
      aria-label={item.label}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex items-center gap-3 rounded-[12px] px-3 py-2.5 text-sm font-medium transition-all duration-[150ms] ease-out",
        "focus-visible:outline-2 focus-visible:outline-[var(--brand-strong)] focus-visible:outline-offset-2",
        "min-h-[44px]",
        active
          ? "bg-[var(--surface-3)] text-[var(--text)]"
          : "text-[var(--text-dim)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
      )}
    >
      {/* Active indicator */}
      {active && (
        <span
          aria-hidden
          className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-r-full bg-[var(--green-500)]"
        />
      )}

      <Icon
        size={18}
        strokeWidth={active ? 2.5 : 1.8}
        className={cn(
          "shrink-0 transition-colors",
          active ? "text-[var(--brand-strong)]" : "text-current"
        )}
      />

      {!iconOnly && <span className="truncate">{item.label}</span>}

      {!iconOnly && active && (
        <ChevronRight
          size={14}
          strokeWidth={2}
          className="ml-auto text-[var(--brand-strong)] shrink-0"
        />
      )}
    </Link>
  );

  if (iconOnly) {
    return (
      <Tooltip>
        <TooltipTrigger render={content} />
        <TooltipContent side="right" sideOffset={8}>
          {item.label}
        </TooltipContent>
      </Tooltip>
    );
  }


  return content;
}

/* ─── SideRail (≥1024px) ──────────────────────────────────────── */
function SideRail({ iconOnly }: { iconOnly: boolean }) {
  return (
    <aside
      className={cn(
        "hidden lg:flex flex-col shrink-0 h-screen sticky top-0",
        "bg-[var(--surface)] border-r border-[var(--border)]",
        "transition-[width] duration-[150ms] ease-out",
        iconOnly ? "w-[68px]" : "w-[240px]"
      )}
      aria-label="Main navigation"
    >
      {/* Logo / wordmark */}
      <div
        className={cn(
          "flex items-center h-16 shrink-0 px-4 border-b border-[var(--border)]",
          iconOnly ? "justify-center" : "gap-2"
        )}
      >
        <span
          aria-hidden
          className="size-7 rounded-[8px] bg-[var(--green-500)] flex items-center justify-center shrink-0"
        >
          <span className="font-display text-[10px] font-black text-[var(--ink-950)] leading-none">
            iO
          </span>
        </span>
        {!iconOnly && (
          <span className="font-display text-sm font-black text-[var(--text)] tracking-tight">
            InterviewOS
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.href} item={item} iconOnly={iconOnly} />
        ))}
      </nav>

      {/* Bottom user area */}
      <div className="shrink-0 p-3 border-t border-[var(--border)]">
        <button
          className={cn(
            "w-full flex items-center gap-3 rounded-[12px] px-3 py-2.5 min-h-[44px]",
            "text-[var(--text-dim)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]",
            "transition-all duration-[150ms] ease-out",
            "focus-visible:outline-2 focus-visible:outline-[var(--brand-strong)] focus-visible:outline-offset-2",
            iconOnly && "justify-center"
          )}
          aria-label="Open user menu"
        >
          <Avatar className="size-7 shrink-0">
            <AvatarImage src="" alt="User avatar" />
            <AvatarFallback className="bg-[var(--surface-3)] text-[var(--text-dim)] text-xs">
              AK
            </AvatarFallback>
          </Avatar>
          {!iconOnly && (
            <span className="text-sm truncate text-left">Aditya Kumar</span>
          )}
        </button>
      </div>
    </aside>
  );
}

/* ─── Bottom tab bar (≤640px) ────────────────────────────────── */
function BottomTabBar() {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Main navigation"
      className="lg:hidden fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around h-16 border-t border-[var(--border)] bg-[var(--surface)]"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      {NAV_ITEMS.slice(0, 5).map((item) => {
        const active =
          pathname === item.href || pathname.startsWith(item.href + "/");
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-label={item.label}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex flex-col items-center gap-1 px-3 py-2 rounded-[12px] min-h-[44px] min-w-[44px]",
              "text-[11px] font-medium transition-all duration-[150ms] ease-out",
              "focus-visible:outline-2 focus-visible:outline-[var(--brand-strong)] focus-visible:outline-offset-2",
              active ? "text-[var(--brand-strong)]" : "text-[var(--text-dim)]"
            )}
          >
            <Icon size={20} strokeWidth={active ? 2.5 : 1.8} />
            <span className="leading-none">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

/* ─── TopBar (640–1024px) ────────────────────────────────────── */
function TopBar({
  targetRole = "Senior SWE",
}: {
  targetRole?: string;
}) {
  const pathname = usePathname();
  const currentPage = NAV_ITEMS.find(
    (i) => pathname === i.href || pathname.startsWith(i.href + "/")
  );

  return (
    <header className="flex items-center justify-between h-16 px-4 md:px-6 border-b border-[var(--border)] bg-[var(--surface)] shrink-0">
      <div className="flex items-center gap-3">
        {/* Mobile logo */}
        <span
          aria-hidden
          className="lg:hidden size-7 rounded-[8px] bg-[var(--green-500)] flex items-center justify-center shrink-0"
        >
          <span className="font-display text-[10px] font-black text-[var(--ink-950)] leading-none">
            iO
          </span>
        </span>
        <span className="text-sm font-semibold text-[var(--text)] hidden sm:inline">
          {currentPage?.label ?? "InterviewOS"}
        </span>
      </div>

      <div className="flex items-center gap-3">
        {/* Target-role chip */}
        <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[999px] border border-[var(--green-700)] bg-[var(--green-700)]/20 text-[var(--green-300)] text-xs font-medium min-h-[44px]">
          <span
            aria-hidden
            className="size-1.5 rounded-full bg-[var(--green-400)]"
          />
          {targetRole}
        </span>

        {/* Avatar */}
        <button
          aria-label="Open user menu"
          className="rounded-full focus-visible:outline-2 focus-visible:outline-[var(--brand-strong)] focus-visible:outline-offset-2 min-h-[44px] min-w-[44px] flex items-center justify-center"
        >
          <Avatar className="size-8">
            <AvatarImage src="" alt="User avatar" />
            <AvatarFallback className="bg-[var(--surface-3)] text-[var(--text-dim)] text-xs">
              AK
            </AvatarFallback>
          </Avatar>
        </button>
      </div>
    </header>
  );
}

/* ─── AppShell ────────────────────────────────────────────────── */
export default function AppShell({
  children,
  targetRole = "Senior SWE",
}: {
  children: React.ReactNode;
  targetRole?: string;
}) {
  const [collapsed] = useState(false);

  return (
    <div className="flex min-h-screen w-full">
      {/* Side rail: visible on lg+ */}
      <SideRail iconOnly={collapsed} />

      {/* Main content area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar (always visible, but role shifts on lg) */}
        <TopBar targetRole={targetRole} />

        {/* Page content */}
        <main
          id="main-content"
          className="flex-1 overflow-y-auto p-4 md:p-6 lg:p-8 pb-20 lg:pb-8"
        >
          {children}
        </main>
      </div>

      {/* Bottom tab bar: visible on < lg */}
      <BottomTabBar />
    </div>
  );
}
