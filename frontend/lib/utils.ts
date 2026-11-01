import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * cn — clsx for conditionals + tailwind-merge so later classes win.
 * (The previous `cn` npm package did not merge Tailwind conflicts,
 * which made component `className` overrides unreliable.)
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
