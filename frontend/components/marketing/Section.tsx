import React from "react";
import { cn } from "@/lib/utils";

type Tone = "canvas" | "surface" | "ink";

const TONE: Record<Tone, string> = {
  canvas: "bg-[var(--canvas)] text-[var(--text)]",
  surface: "bg-[var(--surface)] text-[var(--text)]",
  ink: "bg-[var(--ink-950)] text-[var(--on-ink)]",
};

export default function Section({
  id,
  tone = "canvas",
  className,
  innerClassName,
  children,
}: {
  id?: string;
  tone?: Tone;
  className?: string;
  innerClassName?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className={cn(TONE[tone], "py-20 lg:py-28", className)}>
      <div className={cn("max-w-6xl mx-auto px-6 lg:px-10", innerClassName)}>
        {children}
      </div>
    </section>
  );
}
