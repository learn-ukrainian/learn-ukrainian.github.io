import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import type { APIRoute } from "astro";

/**
 * Canonical Daily Word pool URL for learner fetches.
 * `/api/lexicon/daily-pool.json` re-exports this route as a compatibility alias.
 */
export const prerender = true;

let cachedDailyPoolJson: string | null = null;

function getDailyPoolJson(): string {
  if (!cachedDailyPoolJson) {
    cachedDailyPoolJson = readFileSync(
      resolve(process.cwd(), "src/data/lexicon-daily-pool.json"),
      "utf8",
    );
  }
  return cachedDailyPoolJson;
}

export const GET: APIRoute = () =>
  new Response(getDailyPoolJson(), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
