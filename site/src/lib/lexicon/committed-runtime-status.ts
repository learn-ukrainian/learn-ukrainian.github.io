import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

import { readSelectedArtifactJson, resolveSelectedArtifactLocations } from "./atlas-artifact-selection.mjs";
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

const statusCache = new Map<string, LexiconRuntimeStatus>();

export function resetCommittedLexiconRuntimeStatusForTests(): void {
  statusCache.clear();
}

/** Build runtime status from committed public projections, without atlas.db. */
export function buildCommittedLexiconRuntimeStatus(root = process.cwd()): LexiconRuntimeStatus {
  const resolvedRoot = resolve(root);
  // The selected artifact set is part of the identity of the status it produces.
  const cacheKey = `${resolveSelectedArtifactLocations(resolvedRoot).mode}:${resolvedRoot}`;
  const cached = statusCache.get(cacheKey);
  if (cached) return cached;

  // The five search/browse artifacts follow the shared selection (committed
  // snapshot, or the pinned set while ATLAS_SEARCH_RUNTIME_TREE is set).
  const searchIndex = readSelectedArtifactJson("lexicon-search-index.json", root);
  const searchAliases = readSelectedArtifactJson("lexicon-search-aliases.json", root);
  const practiceIndexes: Partial<Record<PracticeLevel, unknown>> = {};
  for (const level of PRACTICE_LEVELS) {
    practiceIndexes[level] = readOptionalJson(root, `public/lexicon/practice-index.${level}.json`);
  }

  const status = buildLexiconRuntimeStatus({
    manifest: readOptionalJson(root, "src/data/lexicon-manifest.json"),
    manifestPointer: readJson(root, "src/data/lexicon-manifest.pointer.json"),
    searchIndex,
    searchAliases,
    searchShards: readSelectedArtifactJson("lexicon-search-shards.json", root),
    browseMeta: readSelectedArtifactJson("lexicon-browse-meta.json", root),
    entryModel: getCommittedEntryModelCounts(searchIndex, searchAliases),
    dailyPool: readJson(root, "src/data/lexicon-daily-pool.json"),
    practiceIndexes,
    clozeSources: readJson(root, "src/data/lexicon-practice-cloze-sources.json"),
    reviewedSources: readJson(root, "src/data/lexicon-practice-reviewed-sources.json"),
  });
  statusCache.set(cacheKey, status);
  return status;
}
