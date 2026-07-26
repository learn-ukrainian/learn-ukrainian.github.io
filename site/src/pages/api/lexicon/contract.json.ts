import type { APIRoute } from "astro";
import { buildCommittedLexiconRuntimeStatus } from "../../../lib/lexicon/committed-runtime-status";
import { buildLexiconApiContract } from "../../../lib/lexicon/runtime-contract";

export const prerender = true;

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "public, max-age=3600",
};

export const GET: APIRoute = () => {
  const status = buildCommittedLexiconRuntimeStatus();

  return new Response(JSON.stringify(buildLexiconApiContract(status)), {
    headers: JSON_HEADERS,
  });
};
