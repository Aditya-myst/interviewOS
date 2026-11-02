"use client";

import { useEffect, useRef, useState } from "react";
import type { TaxonomySkill } from "@/lib/taxonomy";
import { usePrefersReducedMotion } from "@/lib/useInView";

/**
 * A helix of the actual curriculum.
 *
 * Why a helix: a grid of 41 pill labels is a wall; a helix is the same information
 * with depth, and it reads as "a body of knowledge turning slowly" rather than "a
 * feature list". Chips turn on their own at a constant speed, pause when you point at
 * one, and each carries the number of curated resources behind it — the real number,
 * from contracts/taxonomy.json, not a decoration.
 *
 * No animation library: a `preserve-3d` stage, one `translateZ` per chip, and a
 * requestAnimationFrame loop that writes a single `rotateY` on the stage. Motion+ sells
 * a prebuilt `<Gallery arrange={helix()} />` — it is a paid component — and the free
 * `motion` package turned out to cost more than it paid for here, because the lockfile
 * had to install platform binaries on every machine.
 *
 * The chips themselves are positioned with plain CSS transforms on their own wrapper
 * elements. That is deliberate: a JS animation library that owns `transform` on the
 * same node would overwrite the 3D placement and stack every chip in one spot.
 */
export default function SkillHelix({
  items,
  radius = 198,
  pitch = 48,
  turns = 2,
}: {
  items: TaxonomySkill[];
  radius?: number;
  pitch?: number;
  /** How many times the coil wraps. Two turns reads as a spiral; one reads as a sag. */
  turns?: number;
}) {
  const reduced = usePrefersReducedMotion();
  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(false);
  const stageRef = useRef<HTMLDivElement>(null);

  pausedRef.current = paused;

  const count = Math.max(items.length, 1);
  const step = (360 * turns) / count;
  const height = count * pitch + 150;

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;

    if (reduced) {
      stage.style.transform = "rotateY(-18deg)";
      return;
    }

    // 7 deg/s, held while a pointer or the keyboard is inside.
    let angle = -18;
    let last = performance.now();
    let raf = requestAnimationFrame(function tick(now) {
      const delta = now - last;
      last = now;
      if (!pausedRef.current) angle = (angle - delta * 0.0069) % 360;
      stage.style.transform = `rotateY(${angle}deg)`;
      raf = requestAnimationFrame(tick);
    });
    return () => cancelAnimationFrame(raf);
  }, [reduced]);

  return (
    // The coil is 620px wide by design; below that it would bleed out of the column
    // (measured: 436px of content in a 390px viewport), so the whole stage is scaled
    // down and the wrapper gives back the matching height. Under 1024px the caller
    // renders a list instead — this is only ever seen at full size.
    <div
      className="relative mx-auto w-full max-w-[620px] overflow-hidden h-[430px] sm:h-[560px] lg:h-[var(--helix-h)]"
      style={{ ["--helix-h" as string]: `${height + 12}px` }}
      onPointerEnter={() => setPaused(true)}
      onPointerLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={() => setPaused(false)}
    >
      {/* soft light behind the helix so the chips have something to sit in */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(58% 46% at 50% 46%, rgba(34,197,94,0.16), rgba(34,197,94,0) 70%)",
        }}
      />

      <div
        className="absolute left-1/2 top-2 w-[620px] -translate-x-1/2 origin-center"
        style={{ height, perspective: "900px" }}
      >
        <div
          ref={stageRef}
          className="absolute inset-0"
          style={{ transformStyle: "preserve-3d", transform: "rotateY(-18deg)" }}
        >
          {items.map((skill, i) => {
            const angle = i * step;
            const top = Math.round((height - count * pitch) / 2) + i * pitch;
            return (
              <div
                key={skill.id}
                className="absolute left-1/2 top-0"
                style={{
                  transformStyle: "preserve-3d",
                  // Counter-rotated so the label faces the viewer: the ring still has
                  // depth (perspective scales the far chips down) but no text is ever
                  // mirrored and the whole coil stays visible.
                  transform: `translate(-50%, ${top}px) rotateY(${angle}deg) translateZ(${radius}px) rotateY(${-angle}deg)`,
                }}
              >
                <div className="flex w-[144px] items-center gap-2 rounded-[999px] border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 shadow-[0_2px_6px_rgba(13,26,19,0.08)]">
                  <span
                    aria-hidden
                    className="size-1.5 shrink-0 rounded-full"
                    style={{
                      background: skill.resources > 0 ? "var(--brand)" : "var(--border-strong)",
                    }}
                  />
                  <span className="truncate type-small font-medium text-[var(--text)]">
                    {skill.name}
                  </span>
                  <span className="ml-auto shrink-0 font-mono type-micro tabular-nums text-[var(--text-dim)]">
                    {skill.resources}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* fade the coil into the page at the top and bottom edges */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-16"
        style={{ background: "linear-gradient(to bottom, var(--canvas), transparent)" }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-20"
        style={{ background: "linear-gradient(to top, var(--canvas), transparent)" }}
      />

      {/* the loop has no ends and no start — say what it is, once, for screen readers */}
      <p className="sr-only">
        Skills with curated resources: {items.map((s) => `${s.name} (${s.resources})`).join(", ")}.
      </p>
    </div>
  );
}
