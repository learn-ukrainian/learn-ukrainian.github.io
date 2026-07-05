/* eslint-env node */
/* global console, process */

import Database from 'better-sqlite3';
import { createWriteStream } from 'node:fs';
import { mkdtemp, rm } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { performance } from 'node:perf_hooks';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, '../..');
const pythonPath = resolve(repoRoot, '.venv/bin/python');
const currentManifestPath = resolve(repoRoot, 'site/src/data/lexicon-manifest.json');
const currentPreloadLimitSeconds = Number(process.env.ATLAS_DB_CURRENT_PRELOAD_LIMIT_SECONDS ?? '30');
const currentOnly = process.argv.includes('--current-only');

function secondsSince(start) {
  return (performance.now() - start) / 1000;
}

function runAtlasDb(manifestPath, dbPath) {
  const start = performance.now();
  const result = spawnSync(
    pythonPath,
    ['-m', 'scripts.atlas.atlas_db', '--manifest', manifestPath, '--db', dbPath],
    {
      cwd: repoRoot,
      encoding: 'utf8',
      maxBuffer: 50 * 1024 * 1024,
    },
  );
  if (result.status !== 0) {
    process.stdout.write(result.stdout ?? '');
    process.stderr.write(result.stderr ?? '');
    throw new Error(`atlas_db failed for ${manifestPath}`);
  }
  return secondsSince(start);
}

function preloadPayloads(dbPath) {
  const start = performance.now();
  const db = new Database(dbPath, { readonly: true, fileMustExist: true });
  try {
    const rows = db
      .prepare(
        `SELECT slug, payload_json
         FROM article_payloads
         WHERE is_public_route = 1
         ORDER BY route_order`,
      )
      .all();
    const bySlug = new Map();
    for (const row of rows) {
      bySlug.set(row.slug, JSON.parse(row.payload_json));
    }
    return { seconds: secondsSince(start), bySlug };
  } finally {
    db.close();
  }
}

function measureGetStaticPaths(bySlug) {
  const start = performance.now();
  const paths = Array.from(bySlug.values()).map((entry) => ({
    params: { lemma: entry.url_slug },
    props: { entry },
  }));
  return { seconds: secondsSince(start), count: paths.length };
}

function writeChunk(stream, chunk) {
  return new Promise((resolveWrite, rejectWrite) => {
    if (stream.write(chunk)) {
      resolveWrite();
      return;
    }
    const onDrain = () => {
      stream.off('error', onError);
      resolveWrite();
    };
    const onError = (error) => {
      stream.off('drain', onDrain);
      rejectWrite(error);
    };
    stream.once('drain', onDrain);
    stream.once('error', onError);
  });
}

async function writeSyntheticManifest(manifestPath, rows) {
  const stream = createWriteStream(manifestPath, { encoding: 'utf8' });
  await writeChunk(
    stream,
    `{"version":"synthetic-${rows}","generated_at":"2026-07-05T00:00:00Z","entries":[`,
  );
  for (let index = 0; index < rows; index += 1) {
    const slug = `atlasword-${index}`;
    const entry = {
      lemma: `atlasword${index}`,
      url_slug: slug,
      gloss: `synthetic entry ${index}`,
      pos: 'noun',
      primary_source: 'synthetic',
      course_usage: [],
      enrichment: {
        cefr: { level: 'A1', source: 'synthetic' },
      },
    };
    await writeChunk(stream, `${index === 0 ? '' : ','}${JSON.stringify(entry)}`);
  }
  await writeChunk(stream, ']}');
  await new Promise((resolveFinish, rejectFinish) => {
    stream.end(resolveFinish);
    stream.once('error', rejectFinish);
  });
}

async function benchmarkDataset(tempDir, label, manifestPath, rowCount) {
  const dbPath = join(tempDir, `${label}.db`);
  const dbBuildSeconds = runAtlasDb(manifestPath, dbPath);
  const preload = preloadPayloads(dbPath);
  const staticPaths = measureGetStaticPaths(preload.bySlug);
  return {
    dataset: label,
    rows: rowCount ?? staticPaths.count,
    dbBuildSeconds,
    preloadSeconds: preload.seconds,
    getStaticPathsSeconds: staticPaths.seconds,
    paths: staticPaths.count,
  };
}

function printTable(results) {
  console.log('atlas_db perf benchmark:');
  console.log('| dataset | rows | DB-build seconds | preload seconds | getStaticPaths seconds | paths |');
  console.log('| --- | ---: | ---: | ---: | ---: | ---: |');
  for (const result of results) {
    console.log(
      `| ${result.dataset} | ${result.rows} | ${result.dbBuildSeconds.toFixed(3)} | ` +
        `${result.preloadSeconds.toFixed(3)} | ${result.getStaticPathsSeconds.toFixed(3)} | ${result.paths} |`,
    );
  }
}

async function main() {
  const tempDir = await mkdtemp(join(tmpdir(), 'atlas-db-bench-'));
  try {
    const results = [await benchmarkDataset(tempDir, 'current', currentManifestPath)];
    if (!currentOnly) {
      for (const rows of [50000, 250000]) {
        const manifestPath = join(tempDir, `synthetic-${rows}.json`);
        await writeSyntheticManifest(manifestPath, rows);
        results.push(await benchmarkDataset(tempDir, `${rows} synthetic`, manifestPath, rows));
      }
    }
    printTable(results);
    const current = results[0];
    if (current.preloadSeconds > currentPreloadLimitSeconds) {
      throw new Error(
        `current preload ${current.preloadSeconds.toFixed(3)}s exceeds ${currentPreloadLimitSeconds}s`,
      );
    }
    console.log(
      `perf gate current preload ${current.preloadSeconds.toFixed(3)}s <= ` +
        `${currentPreloadLimitSeconds}s OK`,
    );
  } finally {
    await rm(tempDir, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
