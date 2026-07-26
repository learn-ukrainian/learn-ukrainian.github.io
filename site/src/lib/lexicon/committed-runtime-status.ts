import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { getCommittedEntryModelCounts } from "./committed-entry-model.ts";
import {
  PRACTICE_LEVELS,
  buildLexiconRuntimeStatus,
  type LexiconRuntimeStatus,
  type PracticeLevel,
} from "./runtime-contract.ts";

function readJson(root: string, relativePath: string): unknown {
  return JSON.parse(readFileSync(resolve(root, relativePath), "utf8"));
}

function readOptionalJson(root: string, relativePath: string): unknown {
  const path = resolve(root, relativePath);
  return existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : undefined;
}

/** Build runtime status from committed public projections, without atlas.db. */
export function buildCommittedLexiconRuntimeStatus(root = process.cwd()): LexiconRuntimeStatus {
  const searchIndex = readJson(root, "src/data/lexicon-search-index.json");
  const searchAliases = readJson(root, "src/data/lexicon-search-aliases.json");
  const practiceIndexes: Partial<Record<PracticeLevel, unknown>> = {};
  for (const level of PRACTICE_LEVELS) {
    practiceIndexes[level] = readOptionalJson(root, `public/lexicon/practice-index.${level}.json`);
  }

  return buildLexiconRuntimeStatus({
    manifest: readOptionalJson(root, "src/data/lexicon-manifest.json"),
    manifestPointer: readJson(root, "src/data/lexicon-manifest.pointer.json"),
    searchIndex,
    searchAliases,
    searchShards: readJson(root, "src/data/lexicon-search-shards.json"),
    browseMeta: readJson(root, "src/data/lexicon-browse-meta.json"),
    entryModel: getCommittedEntryModelCounts(searchIndex, searchAliases),
    dailyPool: readJson(root, "src/data/lexicon-daily-pool.json"),
    practiceIndexes,
    clozeSources: readJson(root, "src/data/lexicon-practice-cloze-sources.json"),
    reviewedSources: readJson(root, "src/data/lexicon-practice-reviewed-sources.json"),
  });
}
