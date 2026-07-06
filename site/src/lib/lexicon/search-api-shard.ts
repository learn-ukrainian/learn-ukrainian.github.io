import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import searchIndex from "../../data/lexicon-search-index.json" with { type: "json" };
import shardManifest from "../../data/lexicon-search-shards.json" with { type: "json" };
import {
  buildSearchRowsByShard,
  type SearchRow,
  type SearchShardManifest,
} from "./search.ts";

export const SEARCH_API_JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "public, max-age=3600",
} as const;

const manifest = shardManifest as SearchShardManifest;
const rows = searchIndex as SearchRow[];

export function getSearchRowsByShard(): Map<string, SearchRow[]> {
  return buildSearchRowsByShard(manifest, rows);
}

export function writeSearchShardFiles(siteRoot: string): number {
  const rowsByShard = getSearchRowsByShard();
  const searchShardDir = resolve(siteRoot, "public/lexicon/search");
  mkdirSync(searchShardDir, { recursive: true });
  for (const [shard, shardRows] of rowsByShard) {
    writeFileSync(
      resolve(searchShardDir, `${shard}.json`),
      `${JSON.stringify(shardRows)}\n`,
      "utf8",
    );
  }
  return rowsByShard.size;
}

export const searchApiStaticPaths = () =>
  Object.keys(manifest.shards).map((shard) => ({
    params: { shard },
  }));

export function searchShardResponse(shard: string | undefined): Response {
  const shardRows = shard ? getSearchRowsByShard().get(shard) : undefined;
  if (!shardRows) return new Response("Not found", { status: 404 });

  return new Response(`${JSON.stringify(shardRows)}\n`, {
    headers: SEARCH_API_JSON_HEADERS,
  });
}
