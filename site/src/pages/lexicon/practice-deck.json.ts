import type { APIRoute } from "astro";
import deck from "../../data/lexicon-practice-deck.json";

export const GET: APIRoute = () =>
  new Response(JSON.stringify(deck), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
