import type { APIRoute } from "astro";
import payload from "../../data/lexicon-search-shards.json";

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "public, max-age=3600",
};

export const GET: APIRoute = () => {
  const { data: _data, ...manifest } = payload as Record<string, unknown>;
  return new Response(JSON.stringify(manifest), { headers: JSON_HEADERS });
};
