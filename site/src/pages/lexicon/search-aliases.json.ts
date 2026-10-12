import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { APIRoute } from "astro";

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
    cachedSearchAliasesJson = readFileSync(
      resolve(process.cwd(), "src/data/lexicon-search-aliases.json"),
      "utf8",
    );
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
