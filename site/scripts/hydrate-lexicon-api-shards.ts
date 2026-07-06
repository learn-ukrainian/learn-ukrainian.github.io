/**
 * Materialize lexicon JSON API shards under public/ for static hosting.
 *
 * Astro 7 + trailingSlash: 'always' breaks prerender for dynamic routes whose
 * final segment embeds a param before ".json" (practice-cloze.[level].json.ts).
 * Pre-generating the JSON files avoids that prerender path while preserving URLs.
 */
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { copyPracticeApiShards } from "../src/lib/lexicon/practice-api-shard.ts";
import { writeSearchShardFiles } from "../src/lib/lexicon/search-api-shard.ts";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(scriptDir, "..");

function hydrate(): void {
  copyPracticeApiShards(siteRoot);
  const searchShardCount = writeSearchShardFiles(siteRoot);
  console.log(
    `✓ lexicon API shards: ${3 * 5} practice files under public/api/lexicon, ${searchShardCount} search shards under public/lexicon/search`,
  );
}

try {
  hydrate();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  console.error(`Failed to hydrate lexicon API shards: ${message}`);
  process.exit(1);
}
