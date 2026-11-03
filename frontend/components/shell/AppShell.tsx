"use client";

import React, { useCallback, useSyncExternalStore } from "react";
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
  ClipboardCheck,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/* ─── Collapse preference: read from localStorage without a hydration flip ───
 * `useSyncExternalStore` gives the server a snapshot of `false` and the client the
 * stored value, so the rail never renders one width and snap to the other. It also
 * keeps two tabs in step, which a plain useState would not.
 */
const SIDEBAR_KEY = "ios.sidebar";
const sidebarListeners = new Set<() => void>();

function subscribeSidebar(onChange: () => void) {
  sidebarListeners.add(onChange);
  window.addEventListener("storage", onChange);
  return () => {
    sidebarListeners.delete(onChange);
    window.removeEventListener("storage", onChange);
  };
}

const readCollapsed = () => window.localStorage.getItem(SIDEBAR_KEY) === "collapsed";
const serverCollapsed = () => false;

function writeCollapsed(next: boolean) {
  window.localStorage.setItem(SIDEBAR_KEY, next ? "collapsed" : "open");
  sidebarListeners.forEach((listener) => listener());
}

/* ─── Nav items ──────────────────────────────────────────────── */
// `ready: false` renders as a disabled row with a "soon" marker instead of a
// link. A dead nav link is worse than an honest one: it turns a demo into a 404.
const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, ready: true },
  { href: "/gap-map", label: "Gap Map", icon: Map, ready: true },
  { href: "/roadmap", label: "Roadmap", icon: Route, ready: true },
  { href: "/assessment", label: "Assess", icon: ClipboardCheck, ready: true },
  { href: "/tutor", label: "Tutor", icon: GraduationCap, ready: false },
  { href: "/interview", label: "Interview", icon: Mic2, ready: true },
  { href: "/report", label: "Report", icon: FileText, ready: true },
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
  const active = item.ready &&
    (pathname === item.href || pathname.startsWith(item.href + "/"));
  const Icon = item.icon;

  if (!item.ready) {
    const dis = (
      <div
        aria-disabled="true"
        title={`${item.label} — not built yet`}
        className={cn(
          "flex items-center gap-3 rounded-[12px] px-3 py-2.5 text-sm font-medium",
          "text-[var(--text-dim)]/55 cursor-not-allowed select-none",
          iconOnly && "justify-center"
        )}
      >
        <Icon size={18} strokeWidth={1.8} aria-hidden />
        {!iconOnly && (
          <>
            <span>{item.label}</span>
            <span className="ml-auto type-micro text-[10px] tracking-[0.08em]">
              soon
            </span>
          </>
        )}
      </div>
    );
    // base-ui trigger takes `render`, not Radix's `asChild`.
    return iconOnly ? (
      <Tooltip>
        <TooltipTrigger render={dis} />
        <TooltipContent side="right" sideOffset={8}>
          {item.label} — not built yet
        </TooltipContent>
      </Tooltip>
    ) : (
      dis
    );
  }

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
function SideRail({
  iconOnly,
  onToggle,
}: {
  iconOnly: boolean;
  onToggle: () => void;
}) {
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
      <nav className="flex-1 overflow-y-auto p-3 space-y-0.5" aria-label="Primary">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.href} item={item} iconOnly={iconOnly} />
        ))}
      </nav>

      {/* Collapse control */}
      <div className="shrink-0 px-3 pb-1">
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={!iconOnly}
          aria-label={iconOnly ? "Expand sidebar" : "Collapse sidebar"}
          title={iconOnly ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "w-full flex items-center gap-3 rounded-[12px] px-3 py-2 min-h-[40px]",
            "type-small text-[var(--text-dim)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]",
            "transition-colors duration-[150ms] ease-out",
            "focus-visible:outline-2 focus-visible:outline-[var(--brand-strong)] focus-visible:outline-offset-2",
            iconOnly && "justify-center px-0"
          )}
        >
          {iconOnly ? <PanelLeftOpen size={17} aria-hidden /> : <PanelLeftClose size={17} aria-hidden />}
          {!iconOnly && <span>Collapse</span>}
        </button>
      </div>

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
        const active = item.ready &&
          (pathname === item.href || pathname.startsWith(item.href + "/"));
        const Icon = item.icon;

        if (!item.ready) {
          return (
            <span
              key={item.href}
              aria-disabled="true"
              className="flex flex-col items-center gap-1 px-3 py-2 rounded-[12px] min-h-[44px] min-w-[44px] text-[11px] font-medium text-[var(--text-dim)]/50 select-none"
            >
              <Icon size={20} strokeWidth={1.8} aria-hidden />
              <span className="leading-none">{item.label}</span>
            </span>
          );
        }

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
function TopBar() {
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
        {/* No target-role chip here: the real role comes from the API and is
            printed in each page header. A hardcoded "AI Engineer" pill was the one
            label on screen that no row backed. */}

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
export default function AppShell({ children }: { children: React.ReactNode }) {
  const collapsed = useSyncExternalStore(subscribeSidebar, readCollapsed, serverCollapsed);
  const toggleSidebar = useCallback(() => writeCollapsed(!readCollapsed()), []);

  return (
    <div className="flex min-h-screen w-full">
      {/* Side rail: visible on lg+ */}
      <SideRail iconOnly={collapsed} onToggle={toggleSidebar} />

      {/* Main content area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Top bar (always visible, but role shifts on lg) */}
        <TopBar />

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
