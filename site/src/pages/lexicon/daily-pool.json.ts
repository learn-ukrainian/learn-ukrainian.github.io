import type { APIRoute } from "astro";
import pool from "../../data/lexicon-daily-pool.json";

/**
 * Canonical Daily Word pool URL for learner fetches.
 * `/api/lexicon/daily-pool.json` re-exports this route as a compatibility alias.
 */
export const prerender = true;

export const GET: APIRoute = () =>
  new Response(JSON.stringify(pool), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
