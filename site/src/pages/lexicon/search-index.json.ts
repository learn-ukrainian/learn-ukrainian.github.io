import type { APIRoute } from "astro";
import { readSelectedArtifactText } from "../../lib/lexicon/atlas-artifact-selection.mjs";

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
    cachedSearchIndexJson = readSelectedArtifactText("lexicon-search-index.json", process.cwd());
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
