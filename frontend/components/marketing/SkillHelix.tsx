"use client";

import { useRef, useState } from "react";
import { motion, useAnimationFrame, useMotionValue, useReducedMotion } from "motion/react";
import type { TaxonomySkill } from "@/lib/taxonomy";

/**
 * A helix of the actual curriculum.
 *
 * Why a helix: a grid of 41 pill labels is a wall; a helix is the same information
 * with depth, and it reads as "a body of knowledge turning slowly" rather than "a
 * feature list". Chips turn on their own at a constant speed, pause when you point at
 * one, and each carries the number of curated resources behind it — the real number,
 * from contracts/taxonomy.json, not a decoration.
 *
 * Built with Motion's free library and three CSS transforms per chip. Motion+ sells a
 * prebuilt `<Gallery arrange={helix()} />`; this is not that (it is a paid component),
 * it is a ring in `preserve-3d` with a `rotateY` timeline. It also costs no WebGL.
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
  const reduced = useReducedMotion();
  const [paused, setPaused] = useState(false);
  const rotateY = useMotionValue(-18);

  // 7°/s, held while a pointer or the keyboard is inside. Driven by a motion value so
  // "pause" is a real pause rather than a CSS animation-play-state workaround.
  useAnimationFrame((_, delta) => {
    if (paused || reduced) return;
    rotateY.set((rotateY.get() - delta * 0.0069) % 360);
  });
  const count = Math.max(items.length, 1);
  const step = (360 * turns) / count;
  const height = count * pitch + 150;
  const frame = useRef<HTMLDivElement>(null);

  return (
    // The coil is 620px wide by design; below that it would bleed out of the column
    // (measured: 436px of content in a 390px viewport). Rather than shrink the chips
    // until the labels are unreadable, the whole stage is scaled down and the wrapper
    // gives back the matching height, so nothing overflows and nothing leaves a gap.
    <div
      ref={frame}
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
        className="absolute left-1/2 top-2 w-[620px] -translate-x-1/2 origin-center scale-[0.6] sm:scale-[0.8] lg:scale-100"
        style={{ height, perspective: "900px" }}
      >
      <motion.div
        className="absolute inset-0"
        style={{ transformStyle: "preserve-3d", rotateY }}
      >
        {items.map((skill, i) => {
          const angle = i * step;
          const top = Math.round((height - count * pitch) / 2) + i * pitch;
          return (
            // The 3D placement is a plain CSS transform on a wrapper. Motion owns
            // `transform` on its own elements, so animating opacity on the same node
            // would silently overwrite rotateY/translateZ and stack every chip in one
            // spot — which is exactly what the first render did.
            <div
              key={skill.id}
              className="absolute left-1/2 top-0"
              style={{
                transformStyle: "preserve-3d",
                transform: `translate(-50%, ${top}px) rotateY(${angle}deg) translateZ(${radius}px) rotateY(${-angle}deg)`,
              }}
            >
              <motion.div
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.55, delay: 0.02 * i, ease: "easeOut" }}
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
              </motion.div>
            </div>
          );
        })}
      </motion.div>
      </div>

      {/* the loop has no ends, so fade top and bottom instead of cutting chips off */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-16"
        style={{
          background: "linear-gradient(to bottom, var(--canvas), rgba(242,240,230,0))",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-16"
        style={{
          background: "linear-gradient(to top, var(--canvas), rgba(242,240,230,0))",
        }}
      />

      <p className="sr-only">
        {items.length} skills in a rotating helix.{" "}
        {items
          .map((s) => `${s.name}: ${s.resources} curated resources`)
          .join("; ")}
        .
      </p>
    </div>
  );
}
