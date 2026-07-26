import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { assertPointerFresh } from './hydrate-manifest.mjs';

const scriptDir = resolve(fileURLToPath(new URL('.', import.meta.url)));
const repoRoot = resolve(scriptDir, '../..');
const REGENERATE_COMMAND = 'make atlas-publish';

const REQUIRED_ARTIFACTS = [
  'site/src/data/lexicon-manifest.pointer.json',
  'site/src/data/lexicon-manifest.fingerprint.json',
  'site/src/data/lexicon-search-index.json',
  'site/src/data/lexicon-search-aliases.json',
  'site/src/data/lexicon-search-shards.json',
  'site/src/data/lexicon-browse-meta.json',
  'site/src/data/lexicon-browse-flagged.json',
  'site/src/data/lexicon-daily-pool.json',
  'site/src/data/lexicon-practice-cloze-sources.json',
  'site/src/data/lexicon-practice-reviewed-sources.json',
];

function requireArtifact(relativePath, missing) {
  if (!existsSync(resolve(repoRoot, relativePath))) missing.push(relativePath);
}

function parseJson(relativePath) {
  return JSON.parse(readFileSync(resolve(repoRoot, relativePath), 'utf8'));
}

function expectedBrowseArtifacts(meta) {
  const shards = meta && typeof meta === 'object' ? meta.browseShards : undefined;
  if (!shards || typeof shards !== 'object' || Array.isArray(shards)) {
    throw new Error('site/src/data/lexicon-browse-meta.json lacks a browseShards object.');
  }

  return Object.entries(shards).map(([letter, shard]) => {
    const path = shard && typeof shard === 'object' ? shard.path : undefined;
    if (
      typeof path !== 'string' ||
      !path.startsWith('/lexicon/browse/') ||
      !path.endsWith('.json')
    ) {
      throw new Error(
        `site/src/data/lexicon-browse-meta.json has an invalid browse shard for ${letter}.`,
      );
    }
    return `site/public${path}`;
  });
}

function failForMissingArtifacts(missing) {
  console.error('Missing required committed Atlas artifact(s):');
  for (const relativePath of missing) console.error(`- ${relativePath}`);
  console.error(`Regenerate and publish them with: ${REGENERATE_COMMAND}`);
  process.exit(1);
}

function main() {
  const missing = [];
  for (const relativePath of REQUIRED_ARTIFACTS) requireArtifact(relativePath, missing);
  if (missing.length > 0) failForMissingArtifacts(missing);

  let browseMeta;
  try {
    browseMeta = parseJson('site/src/data/lexicon-browse-meta.json');
    for (const relativePath of expectedBrowseArtifacts(browseMeta))
      requireArtifact(relativePath, missing);
  } catch (error) {
    console.error(
      `Invalid committed Atlas artifact: ${error instanceof Error ? error.message : String(error)}`,
    );
    console.error(`Regenerate and publish it with: ${REGENERATE_COMMAND}`);
    process.exit(1);
  }
  if (missing.length > 0) failForMissingArtifacts(missing);

  const pointer = parseJson('site/src/data/lexicon-manifest.pointer.json');
  const fingerprint = parseJson('site/src/data/lexicon-manifest.fingerprint.json');
  assertPointerFresh(pointer, fingerprint);
  console.log('✓ committed Atlas artifacts verified (no regeneration performed)');
}

main();
