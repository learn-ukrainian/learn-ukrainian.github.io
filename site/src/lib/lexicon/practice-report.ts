import practicePointer from '../../data/lexicon-practice-deck.pointer.json';
import teacherPointer from '../../data/lexicon-teacher-deck.pointer.json';

export const REPORT_DESTINATION = 'https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/new';
export const REPORT_FIELDS = ['deck', 'version', 'digest', 'item', 'type', 'interface-locale', 'public-prompt-reference-id'] as const;
interface Origin {
  deck: string;
  version: string;
  digest: string;
  item: string;
  reference: string;
  snapshot: string;
  functions: unknown[];
}
const origins = new WeakMap<object, Origin>();
const bundled = import.meta.glob<string>([
  '../../data/practice-zno.*.json', '../../data/practice-error-corrections.json',
  '../../data/practice-mechanics/*.json',
], { query: '?raw', import: 'default' });
const atom = (value: string) => value.length > 0 && value.length <= 240 && /^[\p{L}\p{M}\p{N}._:/’ʼ'-]+$/u.test(value);
const isRecord = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const functions = (value: object) => Object.values(value).filter((v) => typeof v === 'function');
const idOf = (record: Record<string, unknown>): unknown => {
  const key = ['clozeId', 'stressId', 'classifyId', 'paradigmId', 'synonymId', 'paronymId', 'heritageId', 'znoTaskId', 'entryId'].find((k) => typeof record[k] === 'string');
  return key ? record[key] : record.card_id ?? record.id ?? record.lemmaId ?? record.slug;
};
async function digestOf(text: string): Promise<string | null> {
  try {
    const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
    return Array.from(new Uint8Array(hash), (b) => b.toString(16).padStart(2, '0')).join('');
  } catch { return null; }
}
function register(value: unknown, identity: Pick<Origin, 'deck' | 'version' | 'digest'>, path: string): void {
  if (Array.isArray(value)) {
    const ids = value.map((v) => isRecord(v) ? idOf(v) : null);
    const counts = new Map<unknown, number>();
    ids.forEach((id) => counts.set(id, (counts.get(id) ?? 0) + 1));
    value.forEach((v, index) => {
      const id = ids[index];
      if (isRecord(v) && typeof id === 'string' && atom(id) && counts.get(id) === 1) {
        origins.set(v, { ...identity, item: id, reference: `${path}/${index}`, snapshot: JSON.stringify(v), functions: functions(v) });
      }
    });
  } else if (isRecord(value)) {
    for (const [key, child] of Object.entries(value)) {
      if (Array.isArray(child)) register(child, identity, `${path}/${key}`);
    }
  }
}
/** Parses the response consumed by the UI; identity failure never prevents practice. */
export async function parsePublicPracticeJson<T>(text: string, url: string): Promise<T> {
  const digest = await digestOf(text);
  const parsed = JSON.parse(text);
  const pointer = [practicePointer, teacherPointer].find((p) => p.files.some((f) => `/lexicon/${f.path}` === url && (!('published' in f) || f.published)));
  const file = pointer?.files.find((f) => `/lexicon/${f.path}` === url);
  if (digest && pointer && file?.sha256 === digest && file.bytes === new TextEncoder().encode(text).length) {
    register(parsed, { deck: pointer.release_tag, version: pointer.deck_version, digest }, url);
  } else if (digest && url === '/lexicon/daily-pool.json') {
    register(parsed, { deck: 'daily-pool', version: `content-sha256:${digest}`, digest }, url);
  }
  return parsed;
}
/** Bundled records come only from tracked raw imports, never caller-supplied text. */
export async function loadBundledPractice<T>(path: string, project: (data: unknown) => T): Promise<T> {
  const loader = bundled[`../../data/${path}`];
  if (!loader) throw new Error(`Unknown practice artifact: ${path}`);
  const text = await loader();
  const digest = await digestOf(text);
  const value = project(JSON.parse(text));
  const collection = path.startsWith('practice-mechanics/') ? '/cards' : path === 'practice-error-corrections.json' ? '/drills' : '';
  if (digest) register(value, { deck: path, version: `content-sha256:${digest}`, digest }, `site/src/data/${path}${collection}`);
  return value;
}
function originOf(value: object): Origin | undefined {
  const origin = origins.get(value);
  try {
    if (origin && JSON.stringify(value) === origin.snapshot && functions(value).length === origin.functions.length && functions(value).every((f, i) => f === origin.functions[i])) return origin;
  } catch { /* Changed or circular records have no public report identity. */ }
}
export function publicRecordId(value: object): string | null { return originOf(value)?.item ?? null; }
/** Checks every displayed record again, including after disclosure was opened. */
export function practiceReportUrl(records: readonly object[], type: string, locale: 'en' | 'uk', item?: string): string | null {
  const bindings = records.map(originOf);
  const primary = bindings[0];
  if (!primary || !atom(type) || (locale !== 'en' && locale !== 'uk') || bindings.some((b) => !b || b.deck !== primary.deck || b.version !== primary.version)) return null;
  const fields = [primary.deck, primary.version, primary.digest, item ?? primary.item, type, locale, primary.reference];
  if (!fields.every(atom)) return null;
  const url = new URL(REPORT_DESTINATION);
  url.searchParams.set('template', '');
  url.searchParams.set('title', 'Practice item report');
  url.searchParams.set('body', fields.map((v, i) => `${REPORT_FIELDS[i]}: ${encodeURIComponent(v)}`).join('\n'));
  return url.href.length <= 2000 ? url.href : null;
}
