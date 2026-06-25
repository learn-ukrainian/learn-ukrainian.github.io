import type { APIRoute } from "astro";
import index from "../../data/lexicon-search-index.json";

/**
 * Static client-side search index for Word Atlas typeahead.
 *
 * Emits one committed compact record per lemma: `l` (lemma), `s` (url_slug),
 * `g` (gloss), `r` (romanized lemma), `k` (source kind), and optional `c`
 * (CEFR level), so typeahead and browse can run without importing the full
 * manifest into site build.
 */
export const GET: APIRoute = () =>
  new Response(JSON.stringify(index), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
