import type { APIRoute } from "astro";
import index from "../../data/lexicon-search-index.json";

/**
 * Static client-side search index for Word Atlas typeahead.
 *
 * Emits one compact record per approved public article: `l` (display head),
 * `s` (article slug), `g` (gloss), `r` (romanized head), `t` (entry type),
 * and optional `c` (CEFR level). Alias resolvers live in the separate
 * `/lexicon/search-aliases.json` artifact and never add to this entry total.
 */
export const GET: APIRoute = () =>
  new Response(JSON.stringify(index), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
