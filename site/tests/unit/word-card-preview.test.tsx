import { describe, expect, it, vi } from 'vitest';
import '@testing-library/jest-dom/vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { render, screen, cleanup } from '@testing-library/react';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createRequire } from 'node:module';
import schema from '../../../schemas/word-card-v1.schema.json';
import WordCardPreview from '../../src/lexicon/WordCardPreview';
import { compareCurrent, fieldStates, pairCurrent, previewCard } from '../../src/lib/lexicon/word-card-preview';
import { hash, loadCases, previewInputs, record, revisionCases } from '../fixtures/word-card-preview/inputs';
import snapshot from '../fixtures/word-card-preview/current';

const cases = loadCases();
const sample = (name: string) => { const c = cases.find(c => c.name === name); if (!c) throw Error(name); return c; };
const parse = (name: string) => previewCard(sample(name).input, 'controlled');
const mutate = (edit: (c: Record<string, unknown>) => void) => { const c = record(structuredClone(sample('zamok-castle').input)); edit(c); return previewCard(c, 'controlled'); };
const stress = (c: Record<string, unknown>) => record(record(c.fields).stress);

describe('source-bound preview mechanics', () => {
  it('keeps consumed state enums aligned with the canonical schema', () => {
    expect([...fieldStates]).toEqual(schema.$defs.field_resolution.properties.state.enum);
    expect([...fieldStates]).toEqual(schema.$defs.field_resolution.properties.propositions.additionalProperties.properties.state.enum);
  });
  it('checks every in-place example and complete five-group ASCII control', () => {
    expect(cases.filter(c => !c.mutations.length)).toHaveLength(11);
    for (const c of cases.filter(c => !c.mutations.length)) expect(previewCard(c.input, 'controlled').kind).toBe(c.name === 'zamok-legacy-split' ? 'successors' : 'card');
    const card = parse('control-complete');
    expect(card.kind).toBe('card');
    if (card.kind !== 'card') throw Error('No control card');
    render(<WordCardPreview card={card} current={null} compare={false} />);
    for (const group of ['forms', 'stress', 'senses', 'examples', 'citations']) expect(screen.getByRole('region', { name: group })).toBeVisible();
    expect(screen.getByText('EXAMPLE_RAW')).toBeVisible();
    expect(card.fields.find(f => f.group === 'stress')?.raw).toEqual(['CONTROL_RAW']);
    expect(card.fields.every(f => f.raw.every(v => !/[^\x00-\x7f]/.test(JSON.stringify(v))))).toBe(true);
    cleanup();
  });
  it('displays exact raw strings, keeps source citations and escapes untrusted text', () => {
    const card = parse('control-untrusted');
    if (card.kind !== 'card') throw Error('No card');
    expect(card.fields.find(f => f.group === 'stress')?.raw).toEqual(['<script>globalThis.previewInjected=1</script> RAW  A']);
    const html = renderToStaticMarkup(<WordCardPreview card={card} current={null} compare={false} />);
    expect(html).toContain('&lt;script&gt;globalThis.previewInjected=1&lt;/script&gt; RAW  A');
    expect(html).not.toContain('<script>');
    const original = record(sample('zamok-castle').input);
    const assertions = original.assertions;
    if (!Array.isArray(assertions)) throw Error('No assertions');
    const source = record(assertions.find(a => record(a).assertion_id === stress(original).selected));
    const plain = parse('zamok-castle');
    if (plain.kind !== 'card') throw Error('No original');
    const field = plain.fields.find(f => f.group === 'stress');
    expect(field?.raw).toEqual([source.value]);
    expect(field?.citations[0]).toEqual({ assertion_id: source.assertion_id, source_id: source.source_id, snapshot_id: source.snapshot_id, locator: source.locator });
  });
  it.each(['control-conflict', 'control-internal', 'control-sum11'])('withholds selected facts for %s', name => {
    const c = parse(name); if (c.kind !== 'card') throw Error('No card');
    expect(c.fields.find(f => f.group === 'stress')?.raw).toEqual([]);
    expect(c.fields.find(f => f.group === 'stress')?.citations).toEqual([]);
  });
  it('retains unverified state and distinguishes missing from suppressed and successors', () => {
    const c = parse('control-unverified'); if (c.kind !== 'card') throw Error('No card');
    expect(c.fields.find(f => f.group === 'stress')?.state).toBe('unverified');
    expect(parse('control-missing').kind).toBe('card');
    for (const name of ['control-suppressed', 'control-redirected', 'zamok-legacy-split', 'control-malformed', 'control-mismatched']) {
      const card = parse(name); const html = renderToStaticMarkup(<WordCardPreview card={card} current={null} compare />);
      expect(html).not.toContain('data-raw-value');
    }
    expect(parse('control-suppressed')).toEqual({kind: 'suppressed',keys:['atlas0:slug:замок','atlas0:heteronym:замок/за́мок']});
    expect(parse('control-redirected')).toMatchObject({kind: 'successors', ids: ['wc_aaaaaaaaaaaa']});
    expect(previewCard(sample('zamok-castle').input)).toMatchObject({kind: 'unavailable'});
  });
  it('refuses malformed consumed structures and stale field/assertion bindings', () => {
    for (const input of [null, [], true, {}, {schema_version: '2'}, {schema_version:'1',card_id:'wc_a',state:'other'}]) expect(previewCard(input, 'controlled').kind).toBe('unavailable');
    const edits = [
      (c: Record<string, unknown>) => { c.assertions = []; },
      (c: Record<string, unknown>) => { stress(c).values = []; },
      (c: Record<string, unknown>) => { stress(c).selected = 42; },
      (c: Record<string, unknown>) => { stress(c).state = 'conflict'; },
      (c: Record<string, unknown>) => { record(c.fields).invented = stress(c); },
      (c: Record<string, unknown>) => { c.senses = [null]; },
      (c: Record<string, unknown>) => { c.identity = {source_keys: [null]}; },
      (c: Record<string, unknown>) => { c.assertions = [null]; },
      (c: Record<string, unknown>) => { c.unknown = 'unsupported'; },
      (c: Record<string, unknown>) => { c.state = 'split'; c.split_into = []; },
      (c: Record<string, unknown>) => { const p = record(record(c.fields).paradigm); p.propositions = null; },
    ];
    for (const edit of edits) expect(mutate(edit).kind).toBe('unavailable');
    expect(parse('control-mismatched')).toEqual({kind:'unavailable',reason:'Mismatched selected assertion binding',keys:['atlas0:slug:замок','atlas0:heteronym:замок/за́мок']});
    const rejected = mutate(c => { const values = c.assertions; if (!Array.isArray(values)) throw Error('No assertions'); for (const a of values) record(record(a).review).status = 'rejected'; });
    if (rejected.kind !== 'card') throw Error('No rejected card');
    expect(rejected.fields.flatMap(f => f.raw)).toEqual([]);
  });
  it('refuses spelling-only, heteronym-without-snapshot and multiply claimed key pairing', () => {
    const cards = cases.filter(c => !c.mutations.length).map(c => previewCard(c.input, 'controlled'));
    const current = snapshot.records.map(r => r.record);
    expect(pairCurrent(parse('zamok-castle'), cards, current)).toBeNull();
    expect(pairCurrent(parse('zamok-lock'), cards, current)).toBeNull();
    expect(pairCurrent(parse('zamok-settlement'), cards, current)).toBeNull();
    expect(pairCurrent(parse('control-suppressed'), cards, current)).toBeNull();
    const key = parse('kliuch-1'); const paired = pairCurrent(key, cards, current);
    expect(paired).not.toBeNull();
    expect(pairCurrent(key, [...cards, key], current)).toBeNull();
    expect(pairCurrent(key, cards, [])).toBeNull();
    if (!paired || key.kind !== 'card') throw Error('Pair absent');
    const rows = compareCurrent(paired, key);
    for (const field of Object.keys(paired.entry)) expect(rows.map(r => r.path)).toContain(`entry.${field}`);
    expect(new Set(rows.map(r => r.result))).toEqual(new Set(['same', 'differs-unresolved', 'missing']));
    const html = renderToStaticMarkup(<WordCardPreview card={key} current={paired} compare />);
    expect(html).toContain('Better/worse unavailable');
    expect(html).not.toMatch(/data-result="(?:better|worse)"/);
    expect(renderToStaticMarkup(<WordCardPreview card={key} current={null} compare />)).toContain('Unresolved pairing');
  });
  it('freezes exact source/snapshot bytes and case denominator before browser proof', async () => {
    const inputs = await previewInputs();
    expect(inputs).toHaveLength(41);
    const manifest = inputs.map(c => ({name:c.name,source:c.source,fingerprint:c.fingerprint,snapshotHash:c.snapshotHash,kind:c.card.kind}));
    const sourceHashes = cases.map(c => ({name:c.name,source:c.source,sourceHash:c.sourceHash,mutations:c.mutations}));
    const output = process.env.WORD_CARD_PREVIEW_REPORT;
    if (output) writeFileSync(resolve(output), JSON.stringify({schema:hash(readFileSync(resolve('../schemas/word-card-v1.schema.json'))), register:hash(readFileSync(resolve('../docs/sources/permissions-register.yaml'))), routes:82, groups:5, cases:manifest, sourceHashes, revision:revisionCases()},null,2)+'\n');
    expect(hash('abc')).toBe('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  });
  it.each(revisionCases())('preserves literal refusal/source binding for $name', c => {
    const card = previewCard(c.input,'controlled');
    if (c.name.startsWith('f1-')) {
      expect(pairCurrent(card,c.claimants.map(c => previewCard(c,'controlled')),snapshot.records.map(r => r.record))).toBeNull();
      if (c.name.endsWith('-predecessor')) expect(card.keys).toEqual(c.name.includes('-suppressed-') || c.name.includes('-malformed-') ? ['atlas0:slug:замок'] : null);
      if (c.name.includes('-suppressed-') || c.name.includes('-malformed-')) expect(pairCurrent(parse('kliuch-1'),c.claimants.map(c => previewCard(c,'controlled')),snapshot.records.map(r => r.record))).toEqual(snapshot.records[1]?.record);
    } else {
      if (card.kind !== 'card') throw Error('Missing controlled card');
      const f = card.fields.find(f => f.group === 'stress');
      if (c.name.startsWith('f2-ulif-')) {
        expect(f?.raw).toEqual(['за́мок']);
        expect(f?.citations[0]?.assertion_id).toBe('wa_5888b96f6142b2da61ca2973');
      } else {
        expect(f?.raw).toEqual([]); expect(f?.citations).toEqual([]);
        expect(f?.refusal).toBe('Source unavailable for this view');
      }
    }
  });
  it('honors new internal register entries and public-to-internal drift through both bindings', async () => {
    const load: (text:string) => unknown = createRequire(import.meta.url)('js-yaml').load;
    const sources = record(load(readFileSync(resolve('../docs/sources/permissions-register.yaml'),'utf8'))).sources;
    if (!Array.isArray(sources)) throw Error('Missing register sources');
    expect(sources.map(record).filter(s => Array.isArray(s.appears_in) && s.appears_in.includes('internal') && !s.appears_in.includes('site')).map(s => s.id).sort()).toEqual(['pohribnyi_1992','ubertext_freq','ulp_private','zno_nmt']);
    vi.resetModules();
    vi.doMock('../../../docs/sources/permissions-register.yaml?raw', () => ({default:'sources:\n- id: newly_internal\n  appears_in: [internal]\n- id: ulif\n  appears_in: [internal]\n'}));
    try {
      const {previewCard: drifted} = await import('../../src/lib/lexicon/word-card-preview');
      for (const id of ['newly_internal','ulif']) for (const binding of ['source','register']) {
        const c = record(structuredClone(sample('zamok-castle').input));
        if (!Array.isArray(c.assertions)) throw Error('Missing assertions');
        const a = record(c.assertions.find(a => record(a).assertion_id === stress(c).selected));
        Object.assign(a,{source_id:'public_control'}); Object.assign(record(a.licence_ref),{register_source_id:'public_control',appears_in:['site']});
        if (binding === 'source') a.source_id = id; else record(a.licence_ref).register_source_id = id;
        const parsed = drifted(c,'controlled'); if (parsed.kind !== 'card') throw Error('Missing card');
        expect(parsed.fields.find(f => f.group === 'stress')?.raw).toEqual([]);
        expect(parsed.fields.find(f => f.group === 'stress')?.citations).toEqual([]);
      }
    } finally { vi.doUnmock('../../../docs/sources/permissions-register.yaml?raw'); vi.resetModules(); }
  });
});
