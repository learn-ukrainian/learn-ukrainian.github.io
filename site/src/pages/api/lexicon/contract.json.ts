import type { APIRoute } from "astro";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  PRACTICE_LEVELS,
  buildLexiconApiContract,
  buildLexiconRuntimeStatus,
  type PracticeLevel,
} from "../../../lib/lexicon/runtime-contract";
import { getAtlasEntryModelCounts } from "../../../lib/lexicon/atlasDb";

export const prerender = true;

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "public, max-age=3600",
};

function readJson(relativePath: string): unknown {
  return JSON.parse(readFileSync(resolve(process.cwd(), relativePath), "utf8"));
}

function readOptionalJson(relativePath: string): unknown {
  const path = resolve(process.cwd(), relativePath);
  return existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : undefined;
}

export const GET: APIRoute = () => {
  const practiceIndexes: Partial<Record<PracticeLevel, unknown>> = {};
  for (const level of PRACTICE_LEVELS) {
    practiceIndexes[level] = readOptionalJson(`public/lexicon/practice-index.${level}.json`);
  }

  const status = buildLexiconRuntimeStatus({
    manifest: readOptionalJson("src/data/lexicon-manifest.json"),
    manifestPointer: readJson("src/data/lexicon-manifest.pointer.json"),
    searchIndex: readJson("src/data/lexicon-search-index.json"),
    searchAliases: readJson("src/data/lexicon-search-aliases.json"),
    searchShards: readJson("src/data/lexicon-search-shards.json"),
    browseMeta: readJson("src/data/lexicon-browse-meta.json"),
    entryModel: getAtlasEntryModelCounts(),
    dailyPool: readJson("src/data/lexicon-daily-pool.json"),
    practiceIndexes,
    clozeSources: readJson("src/data/lexicon-practice-cloze-sources.json"),
    reviewedSources: readJson("src/data/lexicon-practice-reviewed-sources.json"),
  });

  return new Response(JSON.stringify(buildLexiconApiContract(status)), {
    headers: JSON_HEADERS,
  });
};
