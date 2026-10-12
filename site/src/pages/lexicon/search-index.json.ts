import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { APIRoute } from "astro";

/**
 * Static client-side search index for Word Atlas typeahead.
 *
 * Emits one compact record per approved public article: `l` (display head),
 * `s` (article slug), `g` (gloss), `r` (romanized head), `t` (entry type),
 * and optional `c` (CEFR level). Alias resolvers live in the separate
 * `/lexicon/search-aliases.json` artifact and never add to this entry total.
 *
 * Canonical learner URL. `/api/lexicon/search-index.json` re-exports this route
 * as a compatibility alias.
 */
export const prerender = true;

let cachedSearchIndexJson: string | null = null;

function getSearchIndexJson(): string {
  if (!cachedSearchIndexJson) {
    cachedSearchIndexJson = readFileSync(
      resolve(process.cwd(), "src/data/lexicon-search-index.json"),
      "utf8",
    );
  }
  return cachedSearchIndexJson;
}

export const GET: APIRoute = () =>
  new Response(getSearchIndexJson(), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
