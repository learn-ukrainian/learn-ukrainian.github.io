import { existsSync, readFileSync } from 'node:fs';
import { relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  PINNED_SELECTION_ENV,
  SELECTED_ARTIFACT_NAMES,
  assertSelectedArtifactsComplete,
  browseShardFileNames,
  isPinnedSelection,
  resolveSelectedArtifactLocations,
  selectedArtifactPath,
} from '../src/lib/lexicon/atlas-artifact-selection.mjs';
import { assertPointerFresh } from './hydrate-manifest.mjs';
import { verifyTeacherDeckPointer } from './hydrate-teacher-deck.mjs';

const scriptDir = resolve(fileURLToPath(new URL('.', import.meta.url)));
const siteRoot = resolve(scriptDir, '..');
const repoRoot = resolve(siteRoot, '..');
const REGENERATE_COMMAND = 'make atlas-publish';

// The search/browse artifacts follow the shared selection (#12527): the committed
// snapshot, or the ignored pinned set while ATLAS_SEARCH_RUNTIME_TREE is set.
const selectedRepoPath = (name) => relative(repoRoot, selectedArtifactPath(name, siteRoot));

const REQUIRED_ARTIFACTS = [
  'site/src/data/lexicon-manifest.pointer.json',
  'site/src/data/lexicon-manifest.fingerprint.json',
  ...SELECTED_ARTIFACT_NAMES.map(selectedRepoPath),
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
  const metaPath = selectedRepoPath('lexicon-browse-meta.json');
  const { browseDir } = resolveSelectedArtifactLocations(siteRoot);
  return browseShardFileNames(meta, metaPath).map((file) => relative(repoRoot, resolve(browseDir, file)));
}

function failForMissingArtifacts(missing) {
  console.error(`Missing required ${isPinnedSelection() ? 'pinned' : 'committed'} Atlas artifact(s):`);
  for (const relativePath of missing) console.error(`- ${relativePath}`);
  console.error(
    isPinnedSelection()
      ? `Regenerate them with the pinned hydrate (${PINNED_SELECTION_ENV} set; npm run atlas:build-search).`
      : `Regenerate and publish them with: ${REGENERATE_COMMAND}`,
  );
  process.exit(1);
}

function main() {
  const missing = [];
  for (const relativePath of REQUIRED_ARTIFACTS) requireArtifact(relativePath, missing);
  if (missing.length > 0) failForMissingArtifacts(missing);

  let browseMeta;
  try {
    browseMeta = parseJson(selectedRepoPath('lexicon-browse-meta.json'));
    for (const relativePath of expectedBrowseArtifacts(browseMeta))
      requireArtifact(relativePath, missing);
  } catch (error) {
    console.error(
      `Invalid ${isPinnedSelection() ? 'pinned' : 'committed'} Atlas artifact: ${error instanceof Error ? error.message : String(error)}`,
    );
    console.error(
      isPinnedSelection()
        ? `Regenerate it with the pinned hydrate (${PINNED_SELECTION_ENV} set; npm run atlas:build-search).`
        : `Regenerate and publish it with: ${REGENERATE_COMMAND}`,
    );
    process.exit(1);
  }
  if (missing.length > 0) failForMissingArtifacts(missing);

  // Pinned selection: also reject stale shards and an incomplete set (fail closed, no fallback).
  assertSelectedArtifactsComplete(siteRoot);

  const pointer = parseJson('site/src/data/lexicon-manifest.pointer.json');
  const fingerprint = parseJson('site/src/data/lexicon-manifest.fingerprint.json');
  assertPointerFresh(pointer, fingerprint);
  // Required: the site never builds without the published teacher deck (#8843).
  try {
    verifyTeacherDeckPointer({ pointerPath: resolve(repoRoot, 'site/src/data/lexicon-teacher-deck.pointer.json') });
  } catch (error) {
    console.error(`Invalid teacher deck pointer: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
  console.log(
    `✓ ${isPinnedSelection() ? 'pinned' : 'committed'} Atlas artifacts verified (no regeneration performed)`,
  );
}

main();
