/**
 * Serve the teacher-table practice deck (#8843) from its pinned release asset.
 *
 * `teacher-deck refresh --publish` uploads the published set (manifest, deck,
 * cloze, frozen keys, coverage) as one gzip package to the `atlas-teacher-deck`
 * GitHub release and commits `src/data/lexicon-teacher-deck.pointer.json`. This
 * build step downloads that package, verifies the gzip and package hashes, then
 * every file the pointer marks as published (SHA-256, schema and schema version,
 * deck version, compressed-size budget) and writes it to `public/lexicon/`, where
 * the practice page fetches it only when the teacher deck is selected. Any missing
 * or mismatching piece fails the build instead of a silent 404.
 *
 * Before the first publish there is no pointer: hydration and the committed-artifact
 * check then skip the teacher deck with an explicit log line (and remove stale
 * served copies). Once a pointer exists, everything it pins is enforced.
 */
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { gunzipSync, gzipSync } from 'node:zlib';
import { downloadGzip } from './hydrate-practice-deck.mjs';

// Keep in lockstep with TEACHER_*_GZIP_LIMIT in scripts/audit/generate_practice_deck.py
// (tests/test_teacher_deck_refresh.py asserts the two stay equal).
export const TEACHER_DECK_GZIP_LIMIT = 600_000;
export const TEACHER_CLOZE_GZIP_LIMIT = 560_000;
export const SERVED_FILES = {
  'practice-deck.teacher.json': {
    schema: 'atlas-practice-teacher-deck',
    schemaVersion: 1,
    budget: TEACHER_DECK_GZIP_LIMIT,
  },
  'practice-cloze.teacher.json': {
    schema: 'atlas-practice-teacher-cloze',
    schemaVersion: 1,
    budget: TEACHER_CLOZE_GZIP_LIMIT,
  },
};
const PACKAGE_SCHEMA = 'atlas-practice-teacher-package';
const RELEASE_TAG = 'atlas-teacher-deck';
const RELEASE_DOWNLOAD_PREFIX = 'https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/';
const SHA256_RE = /^[0-9a-f]{64}$/;
const RECOVERY =
  'Build and publish it with: .venv/bin/python -m scripts.lexicon.teacher_deck refresh --docx <teacher master DOCX> --publish';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(scriptDir, '..');
const DEFAULT_POINTER = resolve(siteRoot, 'src/data/lexicon-teacher-deck.pointer.json');
const DEFAULT_TARGET = resolve(siteRoot, 'public/lexicon');

function sha256(data) {
  return createHash('sha256').update(data).digest('hex');
}

export function skipLine(pointerPath) {
  return `teacher deck: skipped — no pointer at ${pointerPath} (the deck has not been published yet). ${RECOVERY}`;
}

/** Structural check of a committed pointer (no download): asset, hashes, schemas, cloze file, budgets. */
export function validatePointer(pointer) {
  for (const key of ['asset_url', 'deck_version', 'gz_sha256', 'package_sha256', 'package_bytes', 'files']) {
    if (!(key in pointer)) throw new Error(`teacher deck pointer lacks ${key}`);
  }
  if (pointer.package_schema_version !== 1) {
    throw new Error('teacher deck pointer package_schema_version must be 1');
  }
  const expectedAsset = `${RELEASE_DOWNLOAD_PREFIX}${RELEASE_TAG}/lexicon-teacher-deck-${pointer.deck_version}.json.gz`;
  if (pointer.asset_url !== expectedAsset) {
    throw new Error(`teacher deck pointer asset_url is not ${expectedAsset}`);
  }
  if (!SHA256_RE.test(String(pointer.gz_sha256)) || !SHA256_RE.test(String(pointer.package_sha256))) {
    throw new Error('teacher deck pointer hashes must be SHA-256 hex digests');
  }
  if (!Array.isArray(pointer.files)) throw new Error('teacher deck pointer files must be a list');
  for (const { name, record, expected } of servedRecords(pointer)) {
    if (!SHA256_RE.test(String(record.sha256)) || !Number.isInteger(record.bytes)) {
      throw new Error(`teacher deck pointer record for ${name} lacks a SHA-256 or byte size`);
    }
    if (!Number.isInteger(record.gzipBytes) || record.gzipBytes > expected.budget) {
      throw new Error(`teacher deck ${name} is ${record.gzipBytes} B gzipped, over its ${expected.budget} B budget`);
    }
  }
  return pointer;
}

export function readPointer(pointerPath = DEFAULT_POINTER) {
  if (!existsSync(pointerPath)) {
    throw new Error(`teacher deck pointer missing: ${pointerPath}. ${RECOVERY}`);
  }
  return validatePointer(JSON.parse(readFileSync(pointerPath, 'utf8')));
}

/**
 * Committed-artifact check (`npm run verify:artifacts`): skip with a log line while
 * the deck is unpublished; otherwise the pointer must pass `validatePointer`.
 */
export function verifyTeacherDeckPointer({ pointerPath = DEFAULT_POINTER, log = console.log } = {}) {
  if (!existsSync(pointerPath)) {
    log(skipLine(pointerPath));
    return { skipped: true };
  }
  return { skipped: false, version: readPointer(pointerPath).deck_version };
}

function servedRecords(pointer) {
  const records = new Map(pointer.files.map((record) => [record.path, record]));
  return Object.entries(SERVED_FILES).map(([name, expected]) => {
    const record = records.get(name);
    if (!record || record.published !== true) {
      throw new Error(`teacher deck pointer does not publish ${name}. ${RECOVERY}`);
    }
    if (record.schema !== expected.schema || record.schemaVersion !== expected.schemaVersion) {
      throw new Error(`teacher deck ${name} has an unexpected schema or schema version`);
    }
    return { name, record, expected };
  });
}

/** Validate one served file against its pointer record; returns nothing, throws on any mismatch. */
function assertServedFile(name, data, record, expected, deckVersion) {
  if (data.length !== record.bytes || sha256(data) !== record.sha256) {
    throw new Error(`teacher deck artifact ${name} does not match its pointer hash. ${RECOVERY}`);
  }
  const payload = JSON.parse(data.toString('utf8'));
  if (payload.schema !== expected.schema || payload.schemaVersion !== expected.schemaVersion) {
    throw new Error(`teacher deck artifact ${name} has an unexpected schema or schema version`);
  }
  if (payload.deckVersion !== deckVersion) {
    throw new Error(`teacher deck artifact ${name} deckVersion differs from the pointer`);
  }
  const compressed = gzipSync(data, { level: 9 }).length;
  if (compressed > expected.budget) {
    throw new Error(`teacher deck artifact ${name} is ${compressed} B gzipped, over its ${expected.budget} B budget`);
  }
  if (name === 'practice-deck.teacher.json' && payload.clozeFile !== 'practice-cloze.teacher.json') {
    throw new Error('teacher deck references an unknown cloze file');
  }
}

/** Parse and verify a downloaded package; return [[name, bytes]] for the served files. */
export function parseTeacherPackage(packageBytes, pointer) {
  if (packageBytes.length !== pointer.package_bytes || sha256(packageBytes) !== pointer.package_sha256) {
    throw new Error('teacher deck package does not match its pointer');
  }
  const payload = JSON.parse(packageBytes.toString('utf8'));
  if (payload.schema !== PACKAGE_SCHEMA || payload.schemaVersion !== 1) {
    throw new Error('teacher deck package schema/version mismatch');
  }
  if (payload.deckVersion !== pointer.deck_version) {
    throw new Error('teacher deck package deckVersion differs from the pointer');
  }
  const contents = new Map(payload.files.map((file) => [file.path, file.content]));
  return servedRecords(pointer).map(({ name, record, expected }) => {
    if (typeof contents.get(name) !== 'string') {
      throw new Error(`teacher deck artifact missing from the package: ${name}. ${RECOVERY}`);
    }
    const data = Buffer.from(contents.get(name), 'utf8');
    assertServedFile(name, data, record, expected, pointer.deck_version);
    return [name, data];
  });
}

function alreadyServed(pointer, targetDir) {
  return servedRecords(pointer).every(({ name, record }) => {
    const path = resolve(targetDir, name);
    if (!existsSync(path)) return false;
    const data = readFileSync(path);
    return data.length === record.bytes && sha256(data) === record.sha256;
  });
}

export async function hydrateTeacherDeck({
  pointerPath = DEFAULT_POINTER,
  targetDir = DEFAULT_TARGET,
  log = console.log,
} = {}) {
  if (!existsSync(pointerPath)) {
    // Unpublished deck: nothing to serve, and never an unverified leftover copy.
    for (const name of Object.keys(SERVED_FILES)) rmSync(resolve(targetDir, name), { force: true });
    log(skipLine(pointerPath));
    return { version: null, downloaded: false, skipped: true };
  }
  const pointer = readPointer(pointerPath);
  if (alreadyServed(pointer, targetDir)) return { version: pointer.deck_version, downloaded: false, skipped: false };
  const gzBytes = await downloadGzip(pointer);
  const files = parseTeacherPackage(gunzipSync(gzBytes), pointer);
  mkdirSync(targetDir, { recursive: true });
  for (const [name, data] of files) writeFileSync(resolve(targetDir, name), data);
  return { version: pointer.deck_version, downloaded: true, skipped: false };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  hydrateTeacherDeck()
    .then(({ version, downloaded, skipped }) => {
      if (!skipped) {
        console.log(`✓ teacher deck ${version} ${downloaded ? 'hydrated' : 'already hydrated'} -> public/lexicon`);
      }
    })
    .catch((error) => {
      console.error(`Failed to hydrate the teacher deck: ${error instanceof Error ? error.message : error}`);
      process.exit(1);
    });
}
