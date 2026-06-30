import type { APIRoute, GetStaticPaths } from "astro";
import searchIndex from "../../../data/lexicon-search-index.json";
import shardManifest from "../../../data/lexicon-search-shards.json";
import {
  searchShardKeysForRow,
  type SearchRow,
  type SearchShardManifest,
} from "../../../lib/lexicon/search";

export const prerender = true;

const JSON_HEADERS = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "public, max-age=3600",
};

const manifest = shardManifest as SearchShardManifest;
const rows = searchIndex as SearchRow[];
const rowsByShard = new Map<string, SearchRow[]>(
  Object.keys(manifest.shards).map((key) => [key, []]),
);

for (const row of rows) {
  for (const key of searchShardKeysForRow(manifest, row)) {
    rowsByShard.get(key)?.push(row);
  }
}

export const getStaticPaths: GetStaticPaths = () =>
  Object.keys(manifest.shards).map((shard) => ({
    params: { shard },
  }));

export const GET: APIRoute = ({ params }) => {
  const shard = params.shard;
  const shardRows = shard ? rowsByShard.get(shard) : undefined;
  if (!shardRows) return new Response("Not found", { status: 404 });

  return new Response(`${JSON.stringify(shardRows)}\n`, {
    headers: JSON_HEADERS,
  });
};
