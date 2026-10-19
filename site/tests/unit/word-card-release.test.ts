import { afterAll, describe, expect, it, vi } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import fs from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { loadWordCardRelease, releaseReportUrl } from '../../src/lib/lexicon/word-card-release';
import WordCardPreview from '../../src/lexicon/WordCardPreview';
import { candidateId, certifiedId, pins, releaseControls, fidelityControls, fidelityRefusals } from '../fixtures/word-card-preview/release-controls';


const scratch = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'release-unit-'));
const controls = { ...releaseControls(scratch), ...fidelityControls(join(scratch, 'fidelity')) };
afterAll(() => rmSync(scratch, { recursive: true }));
const load = (name: string) => {
  const config = controls[name];
  if (!config) throw Error('Missing control');
  return loadWordCardRelease(config);
};

describe('pinned producer release boundary', () => {
  it.each(fidelityRefusals)('refuses unsupported source control %s without silently dropping data', (name, reason) => {
    expect(load(name)).toEqual({ kind: 'unavailable', reason });
  });
  it('preserves supplementary Unicode, safe integers, floats, whitespace and arbitrary safe licence metadata', () => {
    const result = load('faithful');
    expect(result.kind).toBe('release');
    if (result.kind !== 'release') throw Error('Refused faithful release');
    const row = result.rows[1];
    expect(row?.fields[1]?.value).toEqual({ nested: [null, true, false, 0, 9007199254740991, -9007199254740991, 1.25, 'A😀𐐀B', ' A\r\nB '] });
    expect(row?.known_gaps).toEqual([{ nested: ['😀', 9007199254740991] }]);
    expect(row?.fields[1]?.citation.licence.extra).toEqual({ nested: ['𐐀', -9007199254740991, null] });
  });
  it.each(['base', 'json'])('accounts for every exact identity, status, parallel assertion and citation in %s', name => {
    const result = load(name);
    expect(result.kind).toBe('release');
    if (result.kind !== 'release') throw Error('Refused positive release');
    expect(result.rows.map(row => [row.card_id, row.card_version, row.status])).toEqual([
      [certifiedId, 'cv_fa34b32f0e93bece65b966e8', 'CERTIFIED'],
      [candidateId, 'synthetic-candidate-1', 'CANDIDATE'],
    ]);
    expect(result.rows.map(row => row.fields[0]?.value)).toEqual(['fixture-head', 'fixture-head']);
    expect(result.rows.flatMap(row => row.fields)).toHaveLength(6);
    const certified = result.rows[0];
    if (!certified) throw Error('Missing certified card');
    expect(certified.fields.map(f => f.value)).toEqual(['fixture-head', 'permitted-definition', 'parallel-definition']);
    expect(certified.fields[1]?.citation).toEqual({
      source_id: 'ulif', snapshot_id: 'fixture-v1', locator: 'ulif:row:1', source_record_id: null,
      source_record_key: 'ulif:record:1', licence_ref: { register_source_id: 'ulif', register_version: 2 },
      attribution: 'Synthetic ulif edition', licence: { name: 'Fixture terms', spdx: null },
      terms_ref: 'docs/sources/permissions-register.yaml#sources/ulif/terms',
    });
    expect(result.pin).toEqual(name === 'base' ? pins.jsonl : pins.json);
  });
  it.each([
    ['absent', 'Release not configured'], ['missing', 'Missing artifact'],
    ['malformed', 'Malformed manifest'], ['bytes', 'Dataset integrity mismatch'],
    ['replacement', 'Manifest pin mismatch'], ['tamper', 'Manifest pin mismatch'],
    ['status', 'Unknown card status'], ['missing-status', 'Unknown card status'],
    ['citation', 'Missing or malformed field citation'], ['required', 'Missing or malformed card field'],
    ['binding', 'Missing or malformed field citation'], ['licence', 'Missing or malformed field citation'],
    ['duplicate', 'Duplicate card identity'], ['assertion', 'Duplicate assertion identity'],
    ['subject', 'Mismatched assertion subject'], ['count', 'Manifest count mismatch'],
    ['schema', 'Malformed or unsupported manifest'], ['path', 'Malformed or unsupported manifest'],
    ['withdrawal', 'Withdrawal notice integrity mismatch'], ['shape', 'Unsupported dataset input'],
    ['malformed-dataset', 'Malformed dataset'],
  ])('refuses %s at its intended validator', (name, reason) => {
    expect(load(name)).toEqual({ kind: 'unavailable', reason });
  });
  it('returns before reading any configured path or parsing the pin when disabled', () => {
    const spy = vi.spyOn(fs, 'readFileSync');
    expect(load('off')).toEqual({ kind: 'disabled' });
    expect(spy).not.toHaveBeenCalled();
    spy.mockRestore();
  });
  it('refuses incomplete/invalid configuration and mismatched immutable pins without path leakage', () => {
    const base = controls.base;
    if (!base) throw Error('Missing control');
    expect(loadWordCardRelease({ enabled: true, pin: 'invalid' })).toEqual({ kind: 'unavailable', reason: 'Incomplete release configuration' });
    for (const pin of ['{', '{}', JSON.stringify({ ...pins.jsonl, extra: true })]) {
      expect(loadWordCardRelease({ ...base, pin })).toEqual({ kind: 'unavailable', reason: 'Malformed release pin' });
    }
    for (const [pin, reason] of [
      [{ ...pins.jsonl, release_version: 'v9.0.0' }, 'Release version mismatch'],
      [{ ...pins.jsonl, dataset_sha256: '0'.repeat(64) }, 'Dataset pin mismatch'],
    ] as const) expect(loadWordCardRelease({ ...base, pin: JSON.stringify(pin) })).toEqual({ kind: 'unavailable', reason });
  });
  it('accepts hash-bound withdrawal notices and empty replacements without inventing cards', () => {
    expect(load('withdrawal-valid').kind).toBe('release');
    expect(load('empty')).toMatchObject({ kind: 'release', rows: [] });
  });
  it('shows all raw assertions, versions, declared gaps and producer status without inferring resolutions', () => {
    const result = load('base');
    if (result.kind !== 'release') throw Error('Missing release');
    for (const row of result.rows) {
      const card = { kind: 'release-card', row, pin: result.pin } as const;
      const html = renderToStaticMarkup(createElement(WordCardPreview, { card, current: null, compare: true }));
      expect(html).toContain(`data-release-card="${row.card_id}"`);
      expect(html).toContain(row.card_version);
      expect(html).toContain(row.status);
      expect(html).toContain('Synthetic fixture. CERTIFIED exercises the UI branch under test authority only.');
      expect(html).toContain('Unresolved pairing');
      expect(html).not.toContain('data-comparison=');
      expect(html).not.toContain('data-field-state');
      expect(html).not.toContain('<script>');
      expect(html).not.toContain('<img src=x');
      for (const field of row.fields) {
        expect(html).toContain(field.assertion_id);
        const url = new URL(releaseReportUrl(card, field));
        expect(url.origin + url.pathname).toBe('https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/new');
        expect(JSON.parse(url.searchParams.get('body') || '')).toEqual({
          release_version: 'v0.1.0-synthetic', dataset_sha256: pins.jsonl.dataset_sha256,
          card_id: row.card_id, card_version: row.card_version, assertion_id: field.assertion_id, field: field.field,
        });
      }
      const real = renderToStaticMarkup(createElement(WordCardPreview, { card: { ...card, pin: { ...card.pin, provenance: 'producer-declared' } }, current: null, compare: false }));
      expect(real).toContain('Producer-declared status. No publication approval is implied.');
    }
  });
  it('keeps the frozen control denominator and input fingerprints explicit', () => {
    const manifest = JSON.parse(readFileSync('tests/fixtures/word-card-preview/release-jsonl/manifest.json', 'utf8'));
    expect(manifest.input_cards_sha256).toBe('a28725cd0f60cace922b2e9d2272a0d06121516cc9755277fbcb098c817da6af');
  });
});
