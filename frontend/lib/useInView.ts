"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

/**
 * The two browser APIs the charts actually needed.
 *
 * `motion` was added for `whileInView`, `pathLength` drawing and `useReducedMotion`.
 * Those are three small things: an IntersectionObserver, an SVG attribute the browser
 * has supported since 2015, and a media query. Adding a package for them meant a
 * lockfile that had to install platform-specific binaries on every machine — and on
 * the target Windows machine it did not. This file is the whole animation dependency
 * now.
 */

/** Fires once when the element first scrolls into view. */
export function useInView<T extends Element>(margin = "-60px") {
  const ref = useRef<T | null>(null);
  // Lazy init instead of "set it in an effect": a browser without IntersectionObserver
  // gets the finished chart on the first paint rather than one that never draws.
  const [inView, setInView] = useState(
    () => typeof window !== "undefined" && typeof IntersectionObserver === "undefined",
  );

  useEffect(() => {
    const node = ref.current;
    if (!node || inView || typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setInView(true);
            observer.disconnect();
          }
        }
      },
      { rootMargin: margin },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [inView, margin]);

  return { ref, inView };
}

const REDUCED_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeReducedMotion(onChange: () => void) {
  const query = window.matchMedia(REDUCED_QUERY);
  query.addEventListener("change", onChange);
  return () => query.removeEventListener("change", onChange);
}

/** True when the visitor asked the OS for less motion. Re-evaluates on change. */
export function usePrefersReducedMotion(): boolean {
  // useSyncExternalStore rather than effect-then-setState: the media query is an
  // external store, and lint is right that reading it in an effect and calling
  // setState causes a second render pass for no reason.
  return useSyncExternalStore(
    subscribeReducedMotion,
    () => window.matchMedia(REDUCED_QUERY).matches,
    () => false,
  );
}
