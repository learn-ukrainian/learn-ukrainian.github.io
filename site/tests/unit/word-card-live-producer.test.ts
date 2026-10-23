import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { loadWordCardRelease } from '../../src/lib/lexicon/word-card-release';
import type { ReleaseResult, ReleaseRow } from '../../src/lib/lexicon/word-card-release';

// Literal contract from the original controlled inputs, never from live output.
const vesum = {
  source_id: 'vesum', snapshot_id: 'fixture-v1', locator: 'vesum:row:0', source_record_id: null,
  source_record_key: 'vesum:record:0', licence_ref: { register_source_id: 'vesum', register_version: 2 },
  attribution: 'Synthetic vesum edition', licence: { name: 'Fixture terms', spdx: null },
  terms_ref: 'docs/sources/permissions-register.yaml#sources/vesum/terms',
};
const ulif = {
  source_id: 'ulif', snapshot_id: 'fixture-v1', locator: 'ulif:row:1', source_record_id: null,
  source_record_key: 'ulif:record:1', licence_ref: { register_source_id: 'ulif', register_version: 2 },
  attribution: 'Synthetic ulif edition', licence: { name: 'Fixture terms', spdx: null },
  terms_ref: 'docs/sources/permissions-register.yaml#sources/ulif/terms',
};
const parallel = { ...ulif, locator: 'ulif:row:parallel', source_record_key: 'ulif:record:parallel' };
const expectedRows: ReleaseRow[] = [
  {
    card_id: 'wc_0123456789ab', card_kind: 'lexeme', card_version: 'cv_fa34b32f0e93bece65b966e8',
    status: 'CERTIFIED', known_gaps: [], fields: [
      { assertion_id: 'wa_000000000000000000000000', subject: { kind: 'card', id: 'wc_0123456789ab' },
        field: 'spelling', value: 'fixture-head', citation: vesum },
      { assertion_id: 'wa_000000000000000000000001', subject: { kind: 'card', id: 'wc_0123456789ab' },
        field: 'definition_uk', value: 'permitted-definition', citation: ulif },
      { assertion_id: 'wa_00000000000000000000000a', subject: { kind: 'card', id: 'wc_0123456789ab' },
        field: 'definition_uk', value: 'parallel-definition', citation: parallel },
    ],
  },
  {
    card_id: 'wc_0123456789ac', card_kind: 'lexeme', card_version: 'synthetic-candidate-1', status: 'CANDIDATE',
    known_gaps: ['Independent linguistic review pending', '<script>globalThis.releaseInjected=1</script>'], fields: [
      { assertion_id: 'wa_000000000000000000000064', subject: { kind: 'card', id: 'wc_0123456789ac' },
        field: 'spelling', value: 'fixture-head', citation: vesum },
      { assertion_id: 'wa_000000000000000000000065', subject: { kind: 'card', id: 'wc_0123456789ac' },
        field: 'definition_uk', value: '<img src=x onerror=globalThis.releaseInjected=1> RAW  A', citation: ulif },
      { assertion_id: 'wa_000000000000000000000066', subject: { kind: 'card', id: 'wc_0123456789ac' },
        field: 'definition_uk', value: 'parallel-definition', citation: parallel },
    ],
  },
];

const scratch = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'live-release-'));
const packages = process.env.ATLAS_LIVE_EXPORT_ROOT || join(scratch, 'packages');
const hash = (bytes: string | Buffer) => createHash('sha256').update(bytes).digest('hex');
beforeAll(() => {
  if (!process.env.ATLAS_LIVE_EXPORT_ROOT) {
    execFileSync(process.env.PYTHON || resolve('../.venv/bin/python'), [
      '-m', 'pytest', '-q', 'tests/test_atlas_live_producer_release.py::test_generate_live_packages',
      '--basetemp', join(scratch, 'pytest'),
    ], { cwd: resolve('..'), timeout: 90_000,
      env: { ...process.env, ATLAS_LIVE_EXPORT_ROOT: packages } });
  }
}, 100_000);
afterAll(() => rmSync(scratch, { recursive: true }));

function assertCompatible(result: ReleaseResult) {
  if (result.kind !== 'release') throw Error(`Expected compatible release; observed ${JSON.stringify(result)}`);
  expect(result.rows, 'Controlled release rows, statuses and all six citation bindings').toEqual(expectedRows);
}

// Change only the selected bytes. Do not parse/reserialize or normalize source values.
function replaceToken(source: string, token: string, replacement: string) {
  expect(source).toContain(token);
  return source.replace(token, replacement);
}

for (const encoding of ['json', 'jsonl']) describe(`current producer ${encoding} through loadWordCardRelease`, () => {
  function loadControl(name: string) {
    const original = join(packages, encoding);
    let dataset = readFileSync(join(original, `word-cards.${encoding}`), 'utf8');
    const manifest = JSON.parse(readFileSync(join(original, 'manifest.json'), 'utf8'));
    expect(manifest.input_cards_sha256).toBe('a28725cd0f60cace922b2e9d2272a0d06121516cc9755277fbcb098c817da6af');
    let artifactPath = original;
    let manifestBytes = readFileSync(join(original, 'manifest.json'));
    if (name !== 'valid') {
      artifactPath = join(scratch, `${encoding}-${name}`);
      mkdirSync(artifactPath);
      switch (name) {
        case 'missing-status':
          dataset = replaceToken(dataset, ',"status":"CANDIDATE"', ''); break;
        case 'unsupported-status':
          dataset = replaceToken(dataset, '"status":"CANDIDATE"', '"status":"WITHDRAWN"'); break;
        case 'lost-identity': {
          const boundary = encoding === 'json' ? dataset.indexOf('},{"card_id"') : dataset.indexOf('\n');
          expect(boundary).toBeGreaterThan(0);
          dataset = encoding === 'json' ? dataset.slice(0, boundary + 1) + ']\n' : dataset.slice(0, boundary + 1);
          break;
        }
        case 'duplicate-identity':
          dataset = replaceToken(dataset, '"card_id":"wc_0123456789ac"', '"card_id":"wc_0123456789ab"'); break;
        case 'missing-citation':
          dataset = replaceToken(dataset, '"citation":{', '"missing_citation":{'); break;
        case 'stale-citation':
          dataset = replaceToken(dataset, '"snapshot_id":"fixture-v1"', '"snapshot_id":"stale"'); break;
        case 'malformed-release': dataset += '{'; break;
        case 'malformed-manifest': break;
        case 'bad-hash': dataset += ' '; break;
        default: throw Error(`Unknown control: ${name}`);
      }
      if (name !== 'bad-hash') {
        manifest.dataset_sha256 = hash(dataset);
        manifest.dataset_bytes = Buffer.byteLength(dataset);
      }
      manifestBytes = Buffer.from(name === 'malformed-manifest' ? '{' : JSON.stringify(manifest) + '\n');
      writeFileSync(join(artifactPath, `word-cards.${encoding}`), dataset);
      writeFileSync(join(artifactPath, 'manifest.json'), manifestBytes);
    }
    const result = loadWordCardRelease({ enabled: true, artifactPath, pin: JSON.stringify({
      release_version: manifest.release_version, dataset_sha256: manifest.dataset_sha256,
      manifest_sha256: hash(manifestBytes), provenance: 'synthetic-fixture',
    }) });
    console.info(JSON.stringify({ encoding, control: name, result }));
    return result;
  }

  it('preserves two same-spelling identities, literal values, statuses and all six citations', () => {
    assertCompatible(loadControl('valid'));
  });
  it.each([
    ['missing-status', 'Unknown card status'], ['unsupported-status', 'Unknown card status'],
    ['lost-identity', 'Manifest count mismatch'], ['duplicate-identity', 'Duplicate card identity'],
    ['missing-citation', 'Missing or malformed field citation'], ['malformed-release', 'Malformed dataset'],
    ['malformed-manifest', 'Malformed manifest'], ['bad-hash', 'Dataset integrity mismatch'],
  ])('refuses %s and fails the same valid-consumer assertion', (name, reason) => {
    const result = loadControl(name);
    expect(result).toEqual({ kind: 'unavailable', reason });
    expect(() => assertCompatible(result)).toThrowError(`Expected compatible release; observed ${JSON.stringify({ kind: 'unavailable', reason })}`);
  });
  it('detects a structurally admitted stale citation at the literal compatibility assertion', () => {
    const result = loadControl('stale-citation');
    expect(result.kind).toBe('release');
    expect(() => assertCompatible(result)).toThrowError('Controlled release rows, statuses and all six citation bindings');
  });
});
