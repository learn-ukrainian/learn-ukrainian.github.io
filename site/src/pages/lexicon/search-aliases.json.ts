import type { APIRoute } from "astro";
import aliases from "../../data/lexicon-search-aliases.json";

/**
 * Public alias resolvers for Word Atlas typeahead.
 *
 * These rows never represent destination pages themselves: each `s` value is
 * the approved article slug to open after a learner matches `a`.
 */
export const GET: APIRoute = () =>
  new Response(JSON.stringify(aliases), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
