import type { APIRoute } from "astro";
import { buildCommittedLexiconRuntimeStatus } from "../../../lib/lexicon/committed-runtime-status";

export const prerender = true;

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "public, max-age=3600",
};

export const GET: APIRoute = () => {
  const status = buildCommittedLexiconRuntimeStatus();

  return new Response(JSON.stringify(status), {
    headers: JSON_HEADERS,
  });
};
