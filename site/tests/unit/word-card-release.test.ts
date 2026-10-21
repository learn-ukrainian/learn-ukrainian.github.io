import { afterAll, describe, expect, it, vi } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import fs from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { attributionGap, attributionLinks, releaseAccounting, loadWordCardRelease, releaseReportUrl } from '../../src/lib/lexicon/word-card-release';
import WordCardPreview from '../../src/lexicon/WordCardPreview';
import { candidateId, certifiedId, pins, releaseControls, fidelityControls, fidelityRefusals, semanticCases, semanticControls, noticeCases, noticeControls, digest } from '../fixtures/word-card-preview/release-controls';


const scratch = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'release-unit-'));
const controls = { ...releaseControls(scratch), ...fidelityControls(join(scratch, 'fidelity')), ...semanticControls(join(scratch, 'semantic')), ...noticeControls(join(scratch, 'notices')) };
afterAll(() => rmSync(scratch, { recursive: true }));
const load = (name: string) => {
  const config = controls[name];
  if (!config) throw Error('Missing control');
  return loadWordCardRelease(config);
};

describe('pinned producer release boundary', () => {
  it('measures absent classes separately and retains exact owned attribution gaps', () => {
    const result = load('base');
    if (result.kind !== 'release') throw Error('Missing release');
    const row = structuredClone(result.rows[0]);
    if (!row?.fields[0] || !row.fields[1]) throw Error('Missing fields');
    row.fields[0].citation = { ...row.fields[0].citation, source_id: 'puls', attribution: 'PULS citation above.' };
    row.fields[1].citation = { ...row.fields[1].citation, source_id: 'vesum', attribution: 'Version <used version> https://vesum.nlp.net.ua/' };
    const stats = releaseAccounting([row]);
    expect(stats).toMatchObject({ cards: 1, citations: 3, declaredGaps: 0, statuses: { CERTIFIED: 1 },
      sources: { puls: 1, vesum: 1, ulif: 1 }, attributionGaps: { puls_reference_placeholder: 1, vesum_version_placeholder: 1 } });
    expect(stats.absentFieldClasses).toContain('examples');
    expect(stats.absentFieldClasses).not.toContain('definition_uk');
    expect(attributionGap({ ...row.fields[0].citation, attribution: 'PULS full credit' })).toBeNull();
    expect(attributionLinks('https://vesum.nlp.net.ua/ https://vesum.nlp.net.ua/ javascript:alert(1) https://evil.invalid/ https://user@vesum.nlp.net.ua/')).toEqual(['https://vesum.nlp.net.ua/']);
    expect(attributionLinks('no URL')).toEqual([]);
    const view = document.createElement('div');
    view.innerHTML = renderToStaticMarkup(createElement(WordCardPreview, { card: { kind: 'release-card', row, pin: result.pin }, current: null, compare: true }));
    expect(Array.from(view.querySelectorAll('[data-source-attribution]')).map(e => e.textContent)).toEqual(row.fields.map(f => f.citation.attribution));
    expect(view.querySelectorAll('[data-attribution-gap]')).toHaveLength(2);
    expect(view.querySelector('[data-source-link]')?.getAttribute('href')).toBe('https://vesum.nlp.net.ua/');
    view.innerHTML = renderToStaticMarkup(createElement(WordCardPreview, { card: { ...result, filteredAssertions: { puls: { filtered_assertions: 29, filter_reasons: { unresolved_mapping: 29 } } } }, current: null, compare: true }));
    expect(view.querySelector('[data-filtered-assertions]')?.textContent).toContain('29');
    expect(view.querySelector('[data-pairing-count]')?.textContent).toBe('0/2 paired; 2/2 explicitly unpaired. 0 actual comparisons.');
    expect(view.querySelectorAll('[data-card-link]')).toHaveLength(2);
  });
  it.each(['json', 'jsonl'] as const)('reports malformed UTF-8 consistently in %s', encoding => {
    const path = join(scratch, `utf8-${encoding}`);
    fs.mkdirSync(path);
    const bytes = Buffer.from([0xff]), manifest = { ...JSON.parse(readFileSync(`tests/fixtures/word-card-preview/release-${encoding}/manifest.json`, 'utf8')),
      dataset_bytes: bytes.length, dataset_sha256: digest(bytes) };
    const manifestBytes = JSON.stringify(manifest);
    fs.writeFileSync(join(path, manifest.dataset_file), bytes);
    fs.writeFileSync(join(path, 'manifest.json'), manifestBytes);
    const pin = JSON.stringify({ ...pins[encoding], dataset_sha256: digest(bytes), manifest_sha256: digest(manifestBytes) });
    expect(loadWordCardRelease({ enabled: true, artifactPath: path, pin })).toEqual({ kind: 'unavailable', reason: 'Malformed dataset' });
  });
  for (const encoding of ['json', 'jsonl']) it.each(noticeCases)(`${encoding} withdrawal notice %s`, (name, reason) => {
    const key = `${encoding}-notice-${name}`, result = load(key);
    if (reason) expect(result).toEqual({ kind: 'unavailable', reason });
    else {
      if (result.kind !== 'release') throw Error('Refused valid notice control');
      expect(result.rows).toHaveLength(2);
      expect(result.rows.reduce((n, row) => n + row.fields.length, 0)).toBe(6);
      expect(result.withdrawalNotice).toEqual(name === 'absent' ? undefined :
        JSON.parse(readFileSync(join(controls[key]?.artifactPath || '', 'withdrawal-notice.json'), 'utf8')));
    }
  });
  for (const encoding of ['json', 'jsonl']) it.each(noticeCases)(`${encoding} empty withdrawal notice %s`, (name, reason) => {
    const config = noticeControls(join(scratch, `empty-${encoding}-${name}`), true)[`${encoding}-notice-${name}`];
    if (!config?.artifactPath) throw Error('Missing empty notice control');
    const result = loadWordCardRelease(config);
    if (reason) expect(result).toEqual({ kind: 'unavailable', reason });
    else {
      if (result.kind !== 'release') throw Error('Refused empty release');
      expect(result.rows).toEqual([]);
      const view = document.createElement('div');
      view.innerHTML = renderToStaticMarkup(createElement(WordCardPreview, { card: result, current: null, compare: true }));
      expect(view.querySelector('[data-release-count]')?.textContent).toBe('0 cards');
      expect(view.querySelector('[data-release-card]')).toBeNull();
      expect(view.querySelector('[aria-label="Withdrawal notice"] pre')?.textContent).toBe(name === 'absent' ? undefined :
        JSON.stringify(JSON.parse(readFileSync(join(config.artifactPath, 'withdrawal-notice.json'), 'utf8')), null, 2));
    }
  });
  for (const encoding of ['json', 'jsonl']) it.each(semanticCases)(`${encoding} semantic $name`, c => {
    const result = load(`${encoding}-${c.name}`);
    if (c.expected === 'refuse') {
      expect(result).toEqual({ kind: 'unavailable', reason: 'Unsupported release value' });
    } else {
      if (result.kind !== 'release') throw Error(`Refused admitted control: ${JSON.stringify(result)}`);
      const row = result.rows[1];
      const value = c.target.includes('value') ? row?.fields[1]?.value : row?.known_gaps[0];
      expect(value).toEqual(JSON.parse(c.target.startsWith('nested-') ? `{"nested":[${c.token}]}` : c.token));
    }
  });
  it.each(['pin', 'manifest'])('refuses lossy numeric %s metadata at the shared boundary', target => {
    const base = controls.base;
    if (!base?.artifactPath || !base.pin) throw Error('Missing control');
    const path = join(scratch, `metadata-${target}`);
    fs.cpSync(base.artifactPath, path, { recursive: true });
    let pin = base.pin;
    if (target === 'pin') pin = pin.replace(/}$/, ',"extra":1e-400}');
    else {
      const file = join(path, 'manifest.json');
      const manifest = fs.readFileSync(file, 'utf8').trimEnd().replace(/}$/, ',"extra":{"n":1.000000000000000000001}}');
      fs.writeFileSync(file, manifest);
      pin = JSON.stringify({ ...JSON.parse(pin), manifest_sha256: digest(manifest) });
    }
    expect(loadWordCardRelease({ enabled: true, artifactPath: path, pin })).toEqual({ kind: 'unavailable', reason: 'Unsupported release value' });
  });
  it.each([
    ['-12.345', -12.345], ['1234500e-4', 123.45], ['0.0012300e+2', 0.123],
    ['1e+' + '0'.repeat(100_000), 1], ['0e' + '9'.repeat(100_000), 0],
    ['1.' + '0'.repeat(100_000), 1], ['0.' + '0'.repeat(100_000) + '1e100001', 1],
    ['1e-' + '9'.repeat(100_000), null], ['1e' + '9'.repeat(100_000), null],
    ['1.' + '0'.repeat(100_000) + '1', null], ['-0.0000000000000000000000000000000000000000000000000000000000000000001e-9999', null],
  ] as const)('compares decimal digits without expanding an exponent (%#)', (token, expected) => {
    const base = controls['json-value-equal-number-0'];
    if (!base?.artifactPath || !base.pin) throw Error('Missing numeric control');
    const path = join(scratch, `decimal-${digest(token)}`);
    fs.mkdirSync(path);
    const data = readFileSync(join(base.artifactPath, 'word-cards.json'), 'utf8').replace('"value":1.0', `"value":${token}`);
    const manifest = { ...JSON.parse(readFileSync(join(base.artifactPath, 'manifest.json'), 'utf8')),
      dataset_sha256: digest(data), dataset_bytes: Buffer.byteLength(data) };
    const manifestBytes = JSON.stringify(manifest);
    fs.writeFileSync(join(path, 'word-cards.json'), data);
    fs.writeFileSync(join(path, 'manifest.json'), manifestBytes);
    const pin = JSON.stringify({ ...JSON.parse(base.pin), dataset_sha256: digest(data), manifest_sha256: digest(manifestBytes) });
    const result = loadWordCardRelease({ enabled: true, artifactPath: path, pin });
    if (expected === null) expect(result).toEqual({ kind: 'unavailable', reason: 'Unsupported release value' });
    else {
      if (result.kind !== 'release') throw Error(`Refused exact decimal: ${JSON.stringify(result)}`);
      expect(result.rows[1]?.fields[1]?.value).toBe(expected);
    }
  });
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
