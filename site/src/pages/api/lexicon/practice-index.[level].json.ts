import type { APIRoute, GetStaticPaths } from "astro";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { PRACTICE_LEVELS, type PracticeLevel } from "../../../lib/lexicon/runtime-contract";

export const prerender = true;

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "public, max-age=3600",
};

function isPracticeLevel(value: string | undefined): value is PracticeLevel {
  return PRACTICE_LEVELS.includes(value as PracticeLevel);
}

export const getStaticPaths: GetStaticPaths = () =>
  PRACTICE_LEVELS.map((level) => ({ params: { level } }));

export const GET: APIRoute = ({ params }) => {
  const level = params.level;
  if (!isPracticeLevel(level)) {
    return new Response(JSON.stringify({ error: "Unknown practice level" }), {
      headers: JSON_HEADERS,
      status: 404,
    });
  }

  return new Response(
    readFileSync(resolve(process.cwd(), `public/lexicon/practice-index.${level}.json`)),
    { headers: JSON_HEADERS },
  );
};
