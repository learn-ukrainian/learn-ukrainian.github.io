import { copyFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { PRACTICE_LEVELS, type PracticeLevel } from "./runtime-contract.ts";

export const PRACTICE_API_JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "public, max-age=3600",
} as const;

export type PracticeShardKind = "practice-index" | "practice-lexemes" | "practice-cloze";

const PRACTICE_KINDS: PracticeShardKind[] = [
  "practice-index",
  "practice-lexemes",
  "practice-cloze",
];

function isPracticeLevel(value: string | undefined): value is PracticeLevel {
  return PRACTICE_LEVELS.includes(value as PracticeLevel);
}

/** Source shards hydrated under public/lexicon/ by hydrate-practice-deck.mjs. */
export function readPracticeShardBytes(kind: PracticeShardKind, level: PracticeLevel): Buffer {
  return readFileSync(resolve(process.cwd(), `public/lexicon/${kind}.${level}.json`));
}

/**
 * Copy practice shards to public/api/lexicon/ for static GitHub Pages hosting.
 * Astro 7 cannot prerender practice-*.{level}.json.ts routes with trailingSlash.
 */
export function copyPracticeApiShards(siteRoot: string): void {
  const lexiconPublicDir = resolve(siteRoot, "public/lexicon");
  const apiLexiconDir = resolve(siteRoot, "public/api/lexicon");
  mkdirSync(apiLexiconDir, { recursive: true });
  for (const kind of PRACTICE_KINDS) {
    for (const level of PRACTICE_LEVELS) {
      const source = resolve(lexiconPublicDir, `${kind}.${level}.json`);
      const target = resolve(apiLexiconDir, `${kind}.${level}.json`);
      if (!existsSync(source)) {
        throw new Error(`Missing practice shard source: ${source}`);
      }
      copyFileSync(source, target);
    }
  }
}

/** Contract helper for tests; production serves pre-generated public/api/lexicon/*.json. */
export function practiceShardResponse(
  kind: PracticeShardKind,
  level: string | undefined,
): Response {
  if (!isPracticeLevel(level)) {
    return new Response(JSON.stringify({ error: "Unknown practice level" }), {
      headers: PRACTICE_API_JSON_HEADERS,
      status: 404,
    });
  }

  return new Response(new Uint8Array(readPracticeShardBytes(kind, level)), {
    headers: PRACTICE_API_JSON_HEADERS,
  });
}

export const practiceApiStaticPaths = () =>
  PRACTICE_LEVELS.map((level) => ({ params: { level } }));
