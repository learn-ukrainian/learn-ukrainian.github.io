import { mkdirSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { readSelectedArtifactJson } from "./atlas-artifact-selection.mjs";
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
function readShardInputs(siteRoot: string): { manifest: SearchShardManifest; rows: SearchRow[] } {
  return {
    manifest: readSelectedArtifactJson("lexicon-search-shards.json", siteRoot) as SearchShardManifest,
    rows: readSelectedArtifactJson("lexicon-search-index.json", siteRoot) as SearchRow[],
  };
}

export function getSearchRowsByShard(siteRoot: string = process.cwd()): Map<string, SearchRow[]> {
  const { manifest, rows } = readShardInputs(siteRoot);
  return buildSearchRowsByShard(manifest, rows);
}

export function writeSearchShardFiles(siteRoot: string): number {
  const rowsByShard = getSearchRowsByShard(siteRoot);
  const searchShardDir = resolve(siteRoot, "public/lexicon/search");
  mkdirSync(searchShardDir, { recursive: true });
  // A shard the selected manifest no longer lists must not ship from an earlier hydrate.
  for (const stale of readdirSync(searchShardDir)) {
    if (stale.endsWith(".json")) rmSync(resolve(searchShardDir, stale));
  }
  for (const [shard, shardRows] of rowsByShard) {
    writeFileSync(
      resolve(searchShardDir, `${shard}.json`),
      `${JSON.stringify(shardRows)}\n`,
      "utf8",
    );
  }
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
