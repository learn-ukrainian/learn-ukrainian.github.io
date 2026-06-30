import type { APIRoute } from "astro";
import index from "../../../data/lexicon-search-index.json";

export const prerender = true;

export const GET: APIRoute = () =>
  new Response(JSON.stringify(index), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
