import { readFileSync } from "node:fs";
import path from "node:path";

/**
 * The curriculum, as the marketing page needs it.
 *
 * Generated from data/taxonomy.yaml + data/curated.yaml by
 * scripts/gen_taxonomy_json.py, so "41 skills" or "19 with resources" in a headline
 * is a number that comes from the same files the product runs on. Read from disk for
 * the same reason lib/fixtures does: it is outside the app root, and import-time
 * resolution across roots is exactly what Turbopack refuses.
 */
export type TaxonomySkill = {
  id: string;
  name: string;
  category: string;
  subtopics: number;
  resources: number;
  teach: number;
};

export type Taxonomy = {
  updated: string | null;
  totals: {
    skills: number;
    subtopics: number;
    resources: number;
    skills_with_resources: number;
  };
  skills: TaxonomySkill[];
};

const CANDIDATES = [
  path.join(process.cwd(), "..", "contracts"),
  path.join(process.cwd(), "contracts"),
];

let cached: Taxonomy | null = null;

export function getTaxonomy(): Taxonomy {
  if (cached) return cached;
  for (const dir of CANDIDATES) {
    try {
      cached = JSON.parse(readFileSync(path.join(dir, "taxonomy.json"), "utf8")) as Taxonomy;
      return cached;
    } catch {
      // try the next candidate
    }
  }
  throw new Error(
    `contracts/taxonomy.json not found. Looked in:\n${CANDIDATES.join("\n")}\n` +
      "Run: python scripts/gen_taxonomy_json.py",
  );
}
