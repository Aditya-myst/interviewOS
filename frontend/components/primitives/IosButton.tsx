"use client";

import React from "react";
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
  children: React.ReactNode;
}

const VARIANT_STYLES: Record<ButtonVariant, string> = {
  primary: [
    "bg-[var(--green-500)] text-[var(--ink-950)]",
    "hover:bg-[var(--green-400)]",
    "active:bg-[var(--green-600)]",
    "focus-visible:outline-2 focus-visible:outline-[var(--green-400)] focus-visible:outline-offset-2",
    "font-semibold",
  ].join(" "),

  secondary: [
    "bg-[var(--ink-800)] text-[var(--text)] border border-[var(--line-strong)]",
    "hover:bg-[var(--ink-700)] hover:border-[var(--line-strong)]",
    "active:bg-[var(--ink-800)]",
    "focus-visible:outline-2 focus-visible:outline-[var(--green-400)] focus-visible:outline-offset-2",
    "font-medium",
  ].join(" "),

  ghost: [
    "bg-transparent text-[var(--text-dim)]",
    "hover:bg-[var(--ink-800)] hover:text-[var(--text)]",
    "active:bg-[var(--ink-700)]",
    "focus-visible:outline-2 focus-visible:outline-[var(--green-400)] focus-visible:outline-offset-2",
    "font-medium",
  ].join(" "),

  danger: [
    "bg-[var(--weak)]/10 text-[var(--weak)] border border-[var(--weak)]/25",
    "hover:bg-[var(--weak)]/20",
    "active:bg-[var(--weak)]/25",
    "focus-visible:outline-2 focus-visible:outline-[var(--weak)] focus-visible:outline-offset-2",
    "font-medium",
  ].join(" "),
};

const SIZE_STYLES: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs rounded-[12px] gap-1.5",
  md: "h-11 px-4 text-sm rounded-[12px] gap-2",
  lg: "min-h-[44px] h-[52px] px-5 text-base rounded-[12px] gap-2.5",
};

const ARROW_SIZE: Record<ButtonSize, number> = {
  sm: 12,
  md: 14,
  lg: 16,
};

/**
 * InterviewOS Button — primary | secondary | ghost | danger
 * Supports optional arrow chip (primary) and loading state.
 */
export default function IosButton({
  variant = "primary",
  size = "md",
  arrow = false,
  loading = false,
  disabled,
  className,
  children,
  ...props
}: IosButtonProps) {
  const isDisabled = disabled || loading;
  const showArrow = arrow && variant === "primary";

  return (
    <button
      data-variant={variant}
      disabled={isDisabled}
      className={cn(
        // Base — always Inter Tight, never mono
        "inline-flex items-center justify-center shrink-0 whitespace-nowrap select-none",
        "font-[family-name:var(--font-sans)]",
        "min-h-[44px] min-w-[44px]",
        "transition-all duration-[150ms] ease-out",
        "disabled:opacity-50 disabled:pointer-events-none",
        // Variant
        VARIANT_STYLES[variant],
        // Size
        SIZE_STYLES[size],
        // Arrow chip padding override
        showArrow && "pr-1.5",
        className
      )}
      {...props}
    >
      {loading ? (
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

          {/* Arrow chip — only for primary */}
          {showArrow && (
            <span
              aria-hidden
              className={cn(
                "flex items-center justify-center rounded-full bg-[var(--ink-950)]/20",
                size === "sm" ? "size-5" : size === "md" ? "size-7" : "size-8"
              )}
            >
              <ArrowRight size={ARROW_SIZE[size]} strokeWidth={2.5} />
            </span>
          )}
        </>
      )}
    </button>
  );
}

export { type ButtonVariant, type ButtonSize };
