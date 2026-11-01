"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface IosButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  arrow?: boolean;
  loading?: boolean;
  /** When set, renders a Next.js <Link> with identical styling — never nest
   *  a <button> inside an <a>, that is what this prop exists to avoid. */
  href?: string;
  children: React.ReactNode;
}

/**
 * Light-theme first. Every variant is readable on the cream canvas, and the
 * arrow chip is owned here — callers must never render their own arrow.
 */
const VARIANT_STYLES: Record<ButtonVariant, string> = {
  primary: [
    "bg-[var(--brand)] text-[var(--ink-950)]",
    "hover:bg-[var(--brand-hover)]",
    "active:bg-[var(--green-600)]",
    "focus-visible:outline-2 focus-visible:outline-[var(--brand-strong)] focus-visible:outline-offset-2",
    "font-semibold",
  ].join(" "),

  secondary: [
    "bg-[var(--surface)] text-[var(--text)] border border-[var(--border-strong)]",
    "hover:bg-[var(--surface-2)]",
    "active:bg-[var(--surface-3)]",
    "focus-visible:outline-2 focus-visible:outline-[var(--brand-strong)] focus-visible:outline-offset-2",
    "font-medium",
  ].join(" "),

  ghost: [
    "bg-transparent text-[var(--text-dim)]",
    "hover:bg-[rgba(13,26,19,0.06)] hover:text-[var(--text)]",
    "active:bg-[rgba(13,26,19,0.10)]",
    "focus-visible:outline-2 focus-visible:outline-[var(--brand-strong)] focus-visible:outline-offset-2",
    "font-medium",
  ].join(" "),

  danger: [
    "bg-[var(--weak)]/8 text-[var(--weak)] border border-[var(--weak)]/25",
    "hover:bg-[var(--weak)]/14",
    "active:bg-[var(--weak)]/20",
    "focus-visible:outline-2 focus-visible:outline-[var(--weak)] focus-visible:outline-offset-2",
    "font-medium",
  ].join(" "),
};

const SIZE_STYLES: Record<ButtonSize, string> = {
  sm: "h-9 px-3 text-xs rounded-[12px] gap-1.5",
  md: "h-11 px-4 text-sm rounded-[12px] gap-2",
  lg: "h-[52px] px-5 text-base rounded-[12px] gap-2.5",
};

const ARROW_SIZE: Record<ButtonSize, number> = { sm: 12, md: 14, lg: 16 };

const ARROW_CHIP: Record<ButtonVariant, string> = {
  primary: "bg-[var(--ink-950)]/15 text-[var(--ink-950)]",
  secondary: "bg-[rgba(13,26,19,0.08)] text-[var(--text)]",
  ghost: "bg-[rgba(13,26,19,0.08)] text-[var(--text)]",
  danger: "bg-[var(--weak)]/15 text-[var(--weak)]",
};

export default function IosButton({
  variant = "primary",
  size = "md",
  arrow = false,
  loading = false,
  disabled,
  className,
  href,
  children,
  ...props
}: IosButtonProps) {
  const isDisabled = disabled || loading;

  const classes = cn(
    "inline-flex items-center justify-center shrink-0 whitespace-nowrap select-none",
    "font-[family-name:var(--font-sans)]",
    "min-h-[44px] min-w-[44px]",
    "transition-all duration-[150ms] ease-out",
    "disabled:pointer-events-none disabled:bg-[var(--surface-3)] disabled:text-[var(--text-dim)] disabled:border disabled:border-[var(--border)]",
    VARIANT_STYLES[variant],
    SIZE_STYLES[size],
    arrow && "pr-1.5",
    className
  );

  const content = loading ? (
    <span className="flex items-center gap-2">
      <span
        aria-hidden
        className="size-4 rounded-full border-2 border-current border-t-transparent animate-spin"
      />
      <span>{children}</span>
    </span>
  ) : (
    <>
      <span>{children}</span>
      {arrow && (
        <span
          aria-hidden
          className={cn(
            "flex items-center justify-center rounded-full",
            ARROW_CHIP[variant],
            size === "sm" ? "size-6" : size === "md" ? "size-7" : "size-8"
          )}
        >
          <ArrowRight size={ARROW_SIZE[size]} strokeWidth={2.5} />
        </span>
      )}
    </>
  );

  if (href && !isDisabled) {
    return (
      <Link href={href} data-variant={variant} className={classes}>
        {content}
      </Link>
    );
  }

  return (
    <button
      type={props.type ?? "button"}
      data-variant={variant}
      disabled={isDisabled}
      className={classes}
      {...props}
    >
      {content}
    </button>
  );
}

export { type ButtonVariant, type ButtonSize };
