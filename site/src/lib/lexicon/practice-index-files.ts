/**
 * Shared practice-index shard probe for SSG / catalog readers.
 *
 * Canonical learner files live under `public/lexicon/`. Hydrate also copies
 * them to `public/api/lexicon/` as a compatibility alias (Astro 7 trailingSlash
 * cannot prerender `practice-*.{level}.json.ts`). Prefer the canonical path.
 */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

export interface PracticeIndexItem {
  lemmaId?: string;
  lemma?: string;
}

/** Candidate filesystem paths for one practice-index level (canonical first). */
export function practiceIndexCandidatePaths(dbDir: string, level: string): string[] {
  return [
    resolve(dbDir, `../site/public/lexicon/practice-index.${level}.json`),
    resolve(dbDir, `../site/public/api/lexicon/practice-index.${level}.json`),
  ];
}

/**
 * Read the first readable practice-index shard for `level`.
 * Returns null when no candidate exists or every candidate fails to parse.
 */
export function readPracticeIndexItems(
  dbDir: string,
  level: string,
): PracticeIndexItem[] | null {
  for (const path of practiceIndexCandidatePaths(dbDir, level)) {
    if (!existsSync(path)) continue;
    try {
      const payload = JSON.parse(readFileSync(path, "utf-8")) as {
        items?: PracticeIndexItem[];
      };
      return Array.isArray(payload?.items) ? payload.items : [];
    } catch {
      // try next candidate
    }
  }
  return null;
}
