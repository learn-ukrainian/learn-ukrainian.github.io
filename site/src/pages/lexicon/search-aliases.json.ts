import type { APIRoute } from "astro";
import { readSelectedArtifactText } from "../../lib/lexicon/atlas-artifact-selection.mjs";

/**
 * Public alias resolvers for Word Atlas typeahead.
 *
 * These rows never represent destination pages themselves: each `s` value is
 * the approved article slug to open after a learner matches `a`.
 */
export const prerender = true;

let cachedSearchAliasesJson: string | null = null;

function getSearchAliasesJson(): string {
  if (!cachedSearchAliasesJson) {
    cachedSearchAliasesJson = readSelectedArtifactText("lexicon-search-aliases.json", process.cwd());
  }
  return cachedSearchAliasesJson;
}

export const GET: APIRoute = () =>
  new Response(getSearchAliasesJson(), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
