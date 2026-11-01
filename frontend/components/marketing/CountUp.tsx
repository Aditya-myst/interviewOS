"use client";

import { useEffect, useRef } from "react";

/**
 * Counts from 0 to `to` once on mount.
 * Writes straight to the DOM node (no state, no re-render per frame) and
 * respects prefers-reduced-motion by rendering the final value immediately.
 */
export default function CountUp({
  to,
  suffix = "",
  duration = 1100,
}: {
  to: number;
  suffix?: string;
  duration?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = `${Math.round(eased * to)}${suffix}`;
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    el.textContent = `0${suffix}`;
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, suffix, duration]);

  return (
    <span ref={ref} aria-label={`${to}${suffix}`}>
      {to}
      {suffix}
    </span>
  );
}
