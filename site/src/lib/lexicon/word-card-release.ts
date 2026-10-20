import { createHash } from 'node:crypto';
import fs from 'node:fs';
import { join } from 'node:path';
import { z } from 'astro/zod';
import cardSchema from '../../../../schemas/word-card-v1.schema.json';

const json = z.json();
// Preserve source strings byte for byte; whitespace is only an admission check.
const nonempty = z.string().refine(value => value.trim().length > 0);
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const count = z.number().int().nonnegative();
const pinSchema = z.object({
  release_version: nonempty, dataset_sha256: digest, manifest_sha256: digest,
  provenance: z.enum(['synthetic-fixture', 'producer-declared']),
}).strict();
const manifestSchema = z.object({
  schema_version: z.literal('word-card-dataset.v1'), release_version: nonempty,
  dataset_file: z.enum(['word-cards.json', 'word-cards.jsonl']), dataset_sha256: digest,
  dataset_bytes: count, card_count: count, certified_count: count,
  candidate_count: count, field_citation_count: count,
  withdrawal_notice_sha256: digest.optional(),
});
const citationSchema = z.object({
  source_id: nonempty, snapshot_id: nonempty, locator: nonempty,
  source_record_id: z.string().nullable().optional(), source_record_key: z.string().nullable().optional(),
  licence_ref: z.object({ register_source_id: nonempty, register_version: z.number().int().positive(),
    appears_in: z.array(z.enum(['internal', 'site', 'dataset'])).optional() }).strict(),
  attribution: nonempty, licence: z.object({ name: nonempty }).catchall(json), terms_ref: nonempty,
}).strict().refine(c => c.source_id === c.licence_ref.register_source_id);
const fieldSchema = z.object({
  assertion_id: z.string().regex(new RegExp(cardSchema.$defs.assertion_id.pattern)),
  subject: z.object({ kind: z.enum(['card', 'sense', 'link']), id: nonempty }).strict(),
  field: nonempty, value: json, citation: citationSchema,
}).strict();
const rowSchema = z.object({
  card_id: z.string().regex(new RegExp(cardSchema.$defs.card_id.pattern)),
  card_version: nonempty, card_kind: nonempty.refine(value => cardSchema.properties.card_kind.enum.includes(value)),
  status: z.enum(['CERTIFIED', 'CANDIDATE']), known_gaps: z.array(json), fields: z.array(fieldSchema).min(1),
}).strict();
export type ReleasePin = z.infer<typeof pinSchema>;
export type ReleaseRow = z.infer<typeof rowSchema>;
export type LoadedRelease = { kind: 'release'; pin: ReleasePin; rows: ReleaseRow[]; withdrawalNotice?: z.infer<typeof json> };
export type ReleaseResult = LoadedRelease | { kind: 'disabled' } | { kind: 'unavailable'; reason: string };
export type ReleaseCard = { kind: 'release-card'; row: ReleaseRow } & Pick<LoadedRelease, 'pin' | 'withdrawalNotice'>;

class Refusal extends Error {}
function refuse(reason: string): never { throw new Refusal(reason); }
const hash = (bytes: Buffer) => createHash('sha256').update(bytes).digest('hex');
function read(path: string): Buffer {
  try { return fs.readFileSync(path); } catch { return refuse('Missing artifact'); }
}
function faithfulJson(value: unknown): boolean {
  if (value === null || typeof value === 'boolean') return true;
  if (typeof value === 'string') return !/[\u0000\uD800-\uDFFF]/u.test(value);
  if (typeof value === 'number') return Number.isFinite(value) && (!Number.isInteger(value) || Number.isSafeInteger(value));
  if (Array.isArray(value)) return value.every(faithfulJson);
  return typeof value === 'object' && Object.entries(value).every(([key, item]) =>
    !['__proto__', 'constructor', 'prototype'].includes(key) && faithfulJson(key) && faithfulJson(item));
}
function decimalParts(token: string) {
  const negative = token.startsWith('-');
  const [coefficient = '', exponent = '0'] = (negative ? token.slice(1) : token).toLowerCase().split('e');
  const point = coefficient.indexOf('.');
  const digits = coefficient.replace('.', '');
  let first = 0, end = digits.length;
  while (first < end && digits[first] === '0') first++;
  while (end > first && digits[end - 1] === '0') end--;
  const magnitude = exponent.replace(/^[+-]?0*/, '') || '0';
  return { negative, digits: digits.slice(first, end),
    shift: digits.length - end - (point < 0 ? 0 : coefficient.length - point - 1),
    exponent: (exponent.startsWith('-') && magnitude !== '0' ? '-' : '') + magnitude };
}
function sameDecimal(source: string, displayed: string): boolean {
  const a = decimalParts(source), b = decimalParts(displayed);
  if (!a.digits || !b.digits) return a.digits === b.digits && a.negative === b.negative;
  // Only the displayed exponent enters arithmetic. Source exponents stay text,
  // so arbitrarily written exponents never cause powers or large-integer arithmetic.
  return a.negative === b.negative && a.digits === b.digits &&
    a.exponent === String(Number(b.exponent) + b.shift - a.shift);
}
function losesHtmlText(value: unknown): boolean {
  // HTML drops the first LF after <pre> and normalizes every CR/CRLF to LF.
  return typeof value === 'string' && (value.startsWith('\n') || value.includes('\r'));
}
function decode(bytes: Buffer, reason: string): string {
  try { return new TextDecoder('utf-8', { fatal: true }).decode(bytes); }
  catch { return refuse(reason); }
}
function parse(bytes: Buffer, reason: string): unknown {
  let value: unknown;
  let unsupported = false;
  try {
    value = JSON.parse(decode(bytes, reason),
      (_key: string, item: unknown, context?: { source?: string }): unknown => {
        if (typeof item === 'number' && (!Number.isFinite(item) ||
          typeof context?.source !== 'string' || !sameDecimal(context.source, String(item)))) unsupported = true;
        return item;
      });
  }
  catch { return refuse(reason); }
  if (unsupported || !faithfulJson(value)) refuse('Unsupported release value');
  return value;
}

/** Local build boundary. Disabled previews return before parsing config or reading any path. */
export function loadWordCardRelease(config: { enabled: boolean; artifactPath?: string; pin?: string }): ReleaseResult {
  if (!config.enabled) return { kind: 'disabled' };
  if (!config.artifactPath && !config.pin) return { kind: 'unavailable', reason: 'Release not configured' };
  try {
    if (!config.artifactPath || !config.pin) refuse('Incomplete release configuration');
    const pinResult = pinSchema.safeParse(parse(Buffer.from(config.pin), 'Malformed release pin'));
    if (!pinResult.success) refuse('Malformed release pin');
    const pin = pinResult.data;
    const manifestBytes = read(join(config.artifactPath, 'manifest.json'));
    if (hash(manifestBytes) !== pin.manifest_sha256) refuse('Manifest pin mismatch');
    const manifestResult = manifestSchema.safeParse(parse(manifestBytes, 'Malformed manifest'));
    if (!manifestResult.success) refuse('Malformed or unsupported manifest');
    const manifest = manifestResult.data;
    if (manifest.release_version !== pin.release_version) refuse('Release version mismatch');
    if (manifest.dataset_sha256 !== pin.dataset_sha256) refuse('Dataset pin mismatch');
    const bytes = read(join(config.artifactPath, manifest.dataset_file));
    if (bytes.length !== manifest.dataset_bytes || hash(bytes) !== pin.dataset_sha256) refuse('Dataset integrity mismatch');
    let withdrawalNotice: LoadedRelease['withdrawalNotice'];
    if (manifest.withdrawal_notice_sha256) {
      const noticeBytes = read(join(config.artifactPath, 'withdrawal-notice.json'));
      if (hash(noticeBytes) !== manifest.withdrawal_notice_sha256) refuse('Withdrawal notice integrity mismatch');
      const notice = z.object({
        schema_version: z.literal('word-card-withdrawal.v1'), previous_release_version: nonempty,
        previous_dataset_sha256: digest, replacement_release_version: nonempty, replacement_dataset_sha256: digest,
        withdrawal: z.object({ selector: z.object({ source_id: nonempty.optional(), locator: nonempty.optional() })
          .strict().refine(s => s.source_id !== undefined || s.locator !== undefined), justification: nonempty }).strict(),
        removed_field_citations: count,
      }).catchall(json).safeParse(parse(noticeBytes, 'Malformed withdrawal notice'));
      if (!notice.success) refuse('Malformed or unsupported withdrawal notice');
      if (notice.data.replacement_release_version !== pin.release_version ||
          notice.data.replacement_dataset_sha256 !== pin.dataset_sha256) refuse('Withdrawal notice release mismatch');
      withdrawalNotice = notice.data;
    }
    const raw = manifest.dataset_file === 'word-cards.json' ? parse(bytes, 'Malformed dataset') :
      decode(bytes, 'Malformed dataset').split(/\r?\n/).filter(line => line.trim()).map(line => parse(Buffer.from(line), 'Malformed dataset'));
    if (!Array.isArray(raw)) refuse('Unsupported dataset input');
    const rows = raw.map((value: unknown) => {
      const status = z.object({ status: z.enum(['CERTIFIED', 'CANDIDATE']) }).safeParse(value);
      if (!status.success) refuse('Unknown card status');
      const result = rowSchema.safeParse(value);
      if (!result.success) refuse(result.error.issues.some(i => i.path.includes('citation')) ?
        'Missing or malformed field citation' : 'Missing or malformed card field');
      if (result.data.known_gaps.some(losesHtmlText) || result.data.fields.some(field => losesHtmlText(field.value))) {
        refuse('Unsupported release value');
      }
      return result.data;
    });
    const ids = new Set<string>();
    const assertions = new Set<string>();
    for (const row of rows) {
      if (ids.has(row.card_id)) refuse('Duplicate card identity');
      ids.add(row.card_id);
      for (const field of row.fields) {
        if (assertions.has(field.assertion_id)) refuse('Duplicate assertion identity');
        assertions.add(field.assertion_id);
        if (field.subject.kind === 'card' && field.subject.id !== row.card_id) refuse('Mismatched assertion subject');
      }
    }
    if (rows.length !== manifest.card_count || assertions.size !== manifest.field_citation_count ||
        rows.filter(r => r.status === 'CERTIFIED').length !== manifest.certified_count ||
        rows.filter(r => r.status === 'CANDIDATE').length !== manifest.candidate_count) refuse('Manifest count mismatch');
    return { kind: 'release', rows, pin, ...(withdrawalNotice === undefined ? {} : { withdrawalNotice }) };
  } catch (error) {
    return { kind: 'unavailable', reason: error instanceof Refusal ? error.message : 'Unsupported release input' };
  }
}

export function releaseReportUrl(card: ReleaseCard, field: ReleaseRow['fields'][number]): string {
  const body = JSON.stringify({
    release_version: card.pin.release_version, dataset_sha256: card.pin.dataset_sha256,
    card_id: card.row.card_id, card_version: card.row.card_version,
    assertion_id: field.assertion_id, field: field.field,
  }, null, 2);
  return `https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/new?body=${encodeURIComponent(body)}`;
}
