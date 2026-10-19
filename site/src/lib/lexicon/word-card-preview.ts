import schema from '../../../../schemas/word-card-v1.schema.json';
import registerText from '../../../../docs/sources/permissions-register.yaml?raw';
import { createRequire } from 'node:module';
import type { EntryRecord } from './atlas-data-source';

export const fieldStates = ['verified', 'single-source', 'variant', 'conflict', 'unverified', 'suppressed'] as const;
type FieldState = typeof fieldStates[number];
type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
type Citation = { assertion_id: string; source_id: string; snapshot_id: string; locator: string };
type Assertion = Citation & { subject: { kind: string; id: string }; field: string; value: Json; value_norm: string; visible: boolean };
export type PreviewField = {
  path: string; group: 'forms' | 'stress' | 'senses' | 'examples'; state: FieldState;
  raw: Json[]; citations: Citation[]; evidence: Json; refusal: string | null;
};
export type PreviewCard = (
  | { kind: 'unavailable'; reason: string }
  | { kind: 'suppressed' }
  | { kind: 'successors'; state: 'redirected' | 'split'; ids: string[] }
  | { kind: 'card'; id: string; fields: PreviewField[] }
) & { keys: string[] | null; claimantId: string | null };
type ReadyCard = Extract<PreviewCard, { kind: 'card' }>;
const cardId = new RegExp(schema.$defs.card_id.pattern);
const assertionId = new RegExp(schema.$defs.assertion_id.pattern);
export type Comparison = { path: string; current: Json; candidate: Json[]; result: 'same' | 'differs-unresolved' | 'missing'; evidence: string };

function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function json(value: unknown, depth = 0): value is Json {
  if (depth > 24) return false;
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return true;
  if (typeof value === 'number') return Number.isFinite(value);
  if (Array.isArray(value)) return value.every(v => json(v, depth + 1));
  return object(value) && Object.entries(value).every(([k, v]) => !['__proto__', 'constructor', 'prototype'].includes(k) && json(v, depth + 1));
}
function strings(value: unknown): value is string[] {
  return Array.isArray(value) && value.every(v => typeof v === 'string');
}
function registerInternalSources(): Set<string> {
  const load: (text: string) => unknown = createRequire(import.meta.url)('js-yaml').load;
  const register = load(registerText);
  if (!object(register) || !Array.isArray(register.sources)) throw Error('Unreadable permissions register');
  return new Set(register.sources.flatMap(source => {
    if (!object(source) || typeof source.id !== 'string' || !strings(source.appears_in) || !source.appears_in.length) throw Error('Malformed register source visibility');
    return source.appears_in.includes('internal') && !source.appears_in.includes('site') ? [source.id] : [];
  }));
}
const internalSources = registerInternalSources();
function state(value: unknown): value is FieldState {
  return fieldStates.some(s => s === value);
}
function selected(value: unknown): string[] {
  if (value === undefined || value === null) return [];
  if (typeof value === 'string') return [value];
  if (strings(value)) return value;
  throw Error('Malformed selection');
}
function identityKeys(input: Record<string, unknown>): string[] {
  if (!object(input.identity) || !Array.isArray(input.identity.source_keys)) throw Error('Missing identity keys');
  return [...new Set(input.identity.source_keys.flatMap(key => {
    if (!object(key) || typeof key.key !== 'string' || typeof key.source_id !== 'string') throw Error('Malformed identity key');
    const asciiLower = (s: string) => s.replace(/[A-Z]/g, c => c.toLowerCase());
    if (asciiLower(key.source_id) !== 'atlas0' && asciiLower(key.key.split(':')[0] ?? '') !== 'atlas0') return [];
    if (key.source_id !== 'atlas0' || !/^atlas0:(slug:[^/]+|heteronym:[^/]+\/[^/]+)$/.test(key.key)) throw Error('Malformed Atlas identity key');
    return [key.key];
  }))];
}
function assertion(value: unknown): Assertion | null {
  if (!object(value) || typeof value.assertion_id !== 'string' || !assertionId.test(value.assertion_id)) throw Error('Malformed assertion');
  if (value.status === 'suppressed') return null;
  if (value.status !== 'active' && value.status !== 'superseded') throw Error('Unknown assertion status');
  if (!object(value.subject) || !['card', 'sense', 'link'].includes(String(value.subject.kind)) || typeof value.subject.id !== 'string' ||
      typeof value.field !== 'string' || !json(value.value) || typeof value.value_norm !== 'string' ||
      typeof value.source_id !== 'string' || !value.source_id || typeof value.snapshot_id !== 'string' || !value.snapshot_id || typeof value.locator !== 'string' || !value.locator ||
      !object(value.licence_ref) || typeof value.licence_ref.register_source_id !== 'string' || !object(value.review) ||
      !schema.$defs.review.properties.status.enum.includes(String(value.review.status))) throw Error('Malformed assertion binding');
  const visibility = value.licence_ref.appears_in;
  if (visibility !== undefined && !strings(visibility)) throw Error('Malformed source visibility');
  return {
    assertion_id: value.assertion_id, source_id: value.source_id, snapshot_id: value.snapshot_id, locator: value.locator,
    subject: { kind: String(value.subject.kind), id: value.subject.id }, field: value.field, value: value.value, value_norm: value.value_norm,
    visible: value.status === 'active' && value.review.status !== 'rejected' && value.source_id !== 'sum11' && value.licence_ref.register_source_id !== 'sum11' &&
      !internalSources.has(value.source_id) && !internalSources.has(value.licence_ref.register_source_id) &&
      (visibility === undefined || visibility.includes('site')),
  };
}

function field(args: { name: string; resolution: unknown; subject: string; kind: 'card' | 'sense'; assertions: Map<string, Assertion> }): PreviewField {
  const { name, resolution: r, subject, kind, assertions } = args;
  if (!object(r) || !state(r.state) || !Array.isArray(r.values) || !['scalar', 'keyed', 'text'].includes(String(r.comparison)) ||
      typeof r.mapping_evidenced !== 'boolean' || !json(r)) throw Error('Malformed field resolution');
  const ids = selected(r.selected);
  if ((r.state === 'conflict' || r.state === 'suppressed') && ids.length) throw Error('Forbidden selected fact');
  const row: PreviewField = {
    path: `${subject}/${name}`, group: name === 'stress' ? 'stress' : name === 'examples' ? 'examples' : kind === 'sense' ? 'senses' : 'forms',
    state: r.state, raw: [], citations: [], evidence: r, refusal: null,
  };
  if (r.state === 'conflict' || r.state === 'suppressed' || !ids.length) return row;
  for (const id of ids) {
    const a = assertions.get(id);
    if (!a || a.subject.kind !== kind || a.subject.id !== subject || a.field !== name) throw Error('Mismatched selected assertion binding');
    const matched = r.values.some(v => object(v) && strings(v.assertion_ids) && v.assertion_ids.includes(id) && v.value_norm === a.value_norm);
    if (!matched) throw Error('Stale field evidence');
    if (!a.visible || name === 'russification_exposed') {
      row.refusal = 'Source unavailable for this view';
      continue;
    }
    if (r.comparison === 'keyed') {
      if (!object(r.propositions)) throw Error('Missing keyed propositions');
      for (const p of Object.values(r.propositions)) {
        if (!object(p) || !state(p.state) || typeof p.mapping_evidenced !== 'boolean') throw Error('Malformed keyed proposition');
        if (p.state === 'conflict' || p.state === 'suppressed' || !selected(p.selected).some(key => ids.includes(key))) {
          row.refusal = 'Keyed selection unavailable';
        }
      }
      if (row.refusal) continue;
    }
    row.raw.push(a.value);
    row.citations.push({ assertion_id: id, source_id: a.source_id, snapshot_id: a.snapshot_id, locator: a.locator });
  }
  return row;
}

/** Consumed-field checks for controlled diagnostics, never a certification validator. */
export function previewCard(input: unknown, mode: 'controlled' | 'real' = 'real'): PreviewCard {
  if (mode === 'real') return { kind: 'unavailable', keys: null, claimantId: null, reason: 'Certified real-card export unavailable. Owner Data, dependency #10516.' };
  let keys: string[] | null = null;
  let claimantId: string | null = null;
  try {
    if (!object(input)) throw Error('Unsupported card input');
    if (typeof input.card_id === 'string' && cardId.test(input.card_id)) claimantId = input.card_id;
    keys = identityKeys(input);
    if (input.schema_version !== '1' || typeof input.card_id !== 'string' || !cardId.test(input.card_id) || Object.keys(input).some(k => !Object.hasOwn(schema.properties, k))) throw Error('Unsupported card input');
    if (input.state === 'suppressed') return { kind: 'suppressed', keys, claimantId };
    if (input.state === 'split' || input.state === 'redirected') {
      const ids = input.state === 'split' ? input.split_into : [input.merged_into];
      if (!strings(ids) || ids.length < (input.state === 'split' ? 2 : 1) || ids.some(id => !cardId.test(id))) throw Error('Malformed successors');
      return { kind: 'successors', state: input.state, ids, keys, claimantId };
    }
    if (input.state !== 'active' || !object(input.fields) || !Array.isArray(input.senses) || !Array.isArray(input.assertions) ||
        !object(input.identity) || !Array.isArray(input.identity.source_keys)) throw Error('Unsupported card structure');
    const assertions = new Map<string, Assertion>();
    const seen = new Set<string>();
    for (const value of input.assertions) {
      const a = assertion(value);
      if (object(value) && typeof value.assertion_id === 'string') {
        if (seen.has(value.assertion_id)) throw Error('Duplicate assertion identity');
        seen.add(value.assertion_id);
      }
      if (a) assertions.set(a.assertion_id, a);
    }
    const fields: PreviewField[] = [];
    const collect = (container: Record<string, unknown>, subject: string, kind: 'card' | 'sense') => {
      const allowed = kind === 'card' ? schema.$defs.card_field_name.enum : schema.$defs.sense_field_name.enum;
      for (const [name, resolution] of Object.entries(container)) {
        if (!allowed.includes(name)) throw Error('Unknown canonical field');
        fields.push(field({ name, resolution, subject, kind, assertions }));
      }
    };
    collect(input.fields, input.card_id, 'card');
    const senses = new Set<string>();
    for (const sense of input.senses) {
      if (!object(sense) || typeof sense.sense_id !== 'string' || !object(sense.fields) || senses.has(sense.sense_id)) throw Error('Malformed sense');
      senses.add(sense.sense_id);
      if (!['active', 'redirected', 'suppressed', 'unsplit'].includes(String(sense.state))) throw Error('Unknown sense state');
      if (sense.state === 'active' || sense.state === 'unsplit') collect(sense.fields, sense.sense_id, 'sense');
    }
    return { kind: 'card', id: input.card_id, keys, claimantId, fields };
  } catch (error) {
    return { kind: 'unavailable', keys, claimantId, reason: error instanceof Error ? error.message : 'Malformed input' };
  }
}

export function pairCurrent(card: PreviewCard, cards: PreviewCard[], current: EntryRecord[]): EntryRecord | null {
  if (card.kind !== 'card' || card.keys === null || card.claimantId !== card.id) return null;
  const owners = new Map<string, PreviewCard | null>();
  const ids = new Set<string>();
  for (const claimant of cards) {
    if (claimant.keys === null || claimant.claimantId === null || ids.has(claimant.claimantId)) return null;
    ids.add(claimant.claimantId);
    for (const key of new Set(claimant.keys)) owners.set(key, owners.has(key) ? null : claimant);
  }
  const claims = new Set(card.keys);
  const key = claims.values().next().value;
  if (claims.size !== 1 || !key?.startsWith('atlas0:slug:')) return null;
  const owner = owners.get(key);
  if (!owner || owner.claimantId !== card.id || new Set(owner.keys).size !== 1) return null;
  let target: EntryRecord | null = null;
  for (const record of current) if (`atlas0:slug:${record.slug}` === key) {
    if (target) return null;
    target = record;
  }
  return target;
}

/** All current record fields remain inspectable, including fields with no candidate mapping. */
export function compareCurrent(current: EntryRecord, card: ReadyCard): Comparison[] {
  const mappings: Record<string, string> = { lemma: 'spelling', pos: 'pos', stress: 'stress', morphology: 'paradigm', gloss: 'english_gloss' };
  return Object.entries(current).flatMap(([root, value]) => {
    const entries = root === 'entry' ? Object.entries(current.entry).map(([k, v]) => [`entry.${k}`, v]) : [[root, value]];
    return entries.flatMap(([path, raw]) => {
      if (typeof path !== 'string' || !json(raw)) return [];
      const name = path.startsWith('entry.') ? mappings[path.slice(6)] : undefined;
      const fields = name ? card.fields.filter(f => f.path === `${card.id}/${name}`) : [];
      const candidate = fields.flatMap(f => f.raw);
      return [{ path, current: raw, candidate, result: candidate.length === 0 ? 'missing' : candidate.length === 1 && JSON.stringify(raw) === JSON.stringify(candidate[0]) ? 'same' : 'differs-unresolved',
        evidence: fields.length ? fields.map(f => `${f.path}: ${f.state}; ${f.citations.map(c => c.assertion_id).join(', ')}`).join('; ') : 'No supported candidate field mapping' } satisfies Comparison];
    });
  });
}
