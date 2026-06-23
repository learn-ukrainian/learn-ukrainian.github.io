import type { APIRoute } from "astro";
import pool from "../../data/lexicon-daily-pool.json";

export const GET: APIRoute = () =>
  new Response(JSON.stringify(pool), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
