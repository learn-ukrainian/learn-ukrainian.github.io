import { createHash } from "node:crypto";
import { mkdirSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { SHARD_INPUT_NAMES, readCertifiedArtifacts, recordDerivedSearchShards } from "./atlas-artifact-selection.mjs";
import {
  buildSearchRowsByShard,
  type SearchRow,
  type SearchShardManifest,
} from "./search.ts";

export const SEARCH_API_JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "public, max-age=3600",
} as const;

/**
 * Read through the shared artifact selection: this module also runs under plain
 * Node (hydrate), where Vite cannot redirect a static JSON import to the pinned set.
 */
function readShardInputs(siteRoot: string): {
  manifest: SearchShardManifest;
  rows: SearchRow[];
  inputDigests: Record<string, string>;
} {
  // Under the pinned selection these bytes must be the ones the pinned-source marker certified.
  const { texts, digests } = readCertifiedArtifacts(SHARD_INPUT_NAMES, siteRoot);
  return {
    manifest: JSON.parse(texts["lexicon-search-shards.json"]!) as SearchShardManifest,
    rows: JSON.parse(texts["lexicon-search-index.json"]!) as SearchRow[],
    inputDigests: digests,
  };
}

export function getSearchRowsByShard(siteRoot: string = process.cwd()): Map<string, SearchRow[]> {
  const { manifest, rows } = readShardInputs(siteRoot);
  return buildSearchRowsByShard(manifest, rows);
}

export function writeSearchShardFiles(siteRoot: string): number {
  const { manifest, rows, inputDigests } = readShardInputs(siteRoot);
  const rowsByShard = buildSearchRowsByShard(manifest, rows);
  const searchShardDir = resolve(siteRoot, "public/lexicon/search");
  mkdirSync(searchShardDir, { recursive: true });
  // A shard the selected manifest no longer lists must not ship from an earlier hydrate.
  for (const stale of readdirSync(searchShardDir)) {
    if (stale.endsWith(".json")) rmSync(resolve(searchShardDir, stale));
  }
  const written: Record<string, string> = {};
  for (const [shard, shardRows] of rowsByShard) {
    const text = `${JSON.stringify(shardRows)}\n`;
    writeFileSync(resolve(searchShardDir, `${shard}.json`), text, "utf8");
    written[`${shard}.json`] = createHash("sha256").update(text, "utf8").digest("hex");
  }
  // Record the certified inputs and the exact bytes written (a no-op unless pinned).
  recordDerivedSearchShards(siteRoot, process.env, { inputs: inputDigests, searchShards: written });
  return rowsByShard.size;
}

export const searchApiStaticPaths = (siteRoot: string = process.cwd()) =>
  Object.keys(readShardInputs(siteRoot).manifest.shards).map((shard) => ({
    params: { shard },
  }));

export function searchShardResponse(shard: string | undefined, siteRoot: string = process.cwd()): Response {
  const shardRows = shard ? getSearchRowsByShard(siteRoot).get(shard) : undefined;
  if (!shardRows) return new Response("Not found", { status: 404 });

  return new Response(`${JSON.stringify(shardRows)}\n`, {
    headers: SEARCH_API_JSON_HEADERS,
  });
}
