import { isValidAtlasSlug } from './atlas-data-source';
import { attributionGap, attributionLinks, type LoadedRelease, type ReleaseRow } from './word-card-release';

type Assertion = ReleaseRow['fields'][number];
export type Credit = { sourceId: string; href: string | null; attribution: string; gap: string | null };
/** One distinct supplied value and every assertion that supplied it. */
export type Fact = { value: string; assertionIds: string[]; credits: Credit[] };
/** More than one fact means the sources differ; all values stay parallel. */
export type FactGroup = { field: string; facts: Fact[] };
export type Sense = { id: string; groups: FactGroup[] };
export type SlotLabel = { text: string; unknown: boolean };
export type ParadigmCell = { forms: string[]; assertionIds: string[] };
export type ParadigmTable = {
  sourceId: string; credits: Credit[]; assertionIds: string[];
  columns: { key: string; label: SlotLabel }[];
  caseRows: { label: string; cells: (ParadigmCell | null)[] }[];
  formRows: { slot: string; label: SlotLabel; cell: ParadigmCell }[];
};
export type ReadableEntry = {
  row: ReleaseRow; ordinal: number; proper: boolean; heading: string; display: string;
  facts: FactGroup[]; senses: Sense[]; paradigms: ParadigmTable[]; other: FactGroup[];
};
export type ReleasePageGroup = { key: string; title: string; entries: ReadableEntry[] };
export type ReleasePage = { kind: 'release-page'; page: ReleasePageGroup } & Pick<LoadedRelease, 'pin' | 'withdrawalNotice'>;
export type Disposition ={ cardId: string; cardKind: string; key: string | null; ordinal: number | null; listed: boolean; reason: string };

/** Display order of card-subject facts. Anything else stays reachable under `other`. */
const CARD_FACTS = ['spelling', 'mwe_form', 'stress', 'pos', 'gender', 'aspect', 'grammatical_label', 'cefr'];
const SENSE_FACTS = ['sense_label', 'synonyms', 'antonyms'];
// Labels from scripts/lexicon/runner/ulif_dictua_parse.py ULIF_LABEL_TAGS; each word VESUM-verified.
const CASES: [string, string][] = [['v_naz', 'Називний'], ['v_rod', 'Родовий'], ['v_dav', 'Давальний'], ['v_zna', 'Знахідний'],
  ['v_oru', 'Орудний'], ['v_mis', 'Місцевий'], ['v_kly', 'Кличний']];
const COMPONENTS: Record<string, string> = {
  inf: 'інфінітив', pres: 'теперішній час', futr: 'майбутній час', past: 'минулий час', impr: 'наказовий спосіб',
  s: 'однина', p: 'множина', m: 'чол. р.', f: 'жін. р.', n: 'сер. р.', 1: '1 особа', 2: '2 особа', 3: '3 особа',
};
const ORDER = ['inf', 'pres', 'futr', 'past', 'impr', 's', 'p', '1', '2', '3', 'm', 'f', 'n'];
const COLUMN_ORDER = ['s', 's.m', 's.f', 's.n', 'p', ''];

export class PageKeyError extends Error {}

/** Page key: the one distinct lowercased card-subject spelling (or mwe_form for MWE cards). */
export function pageKey(row: ReleaseRow): string {
  const field = row.card_kind === 'mwe' ? 'mwe_form' : 'spelling';
  const values = new Set(row.fields.filter(f => f.field === field && f.subject.kind === 'card' && f.subject.id === row.card_id)
    .map(f => typeof f.value === 'string' ? f.value.toLowerCase() : null));
  const [key] = values;
  if (values.size !== 1 || typeof key !== 'string' || !isValidAtlasSlug(key)) throw new PageKeyError('Missing or ambiguous page key');
  return key;
}

export function displayValue(value: Assertion['value']): string {
  if (typeof value === 'string') return value;
  if (Array.isArray(value) && value.every(item => typeof item === 'string')) return value.join(', ');
  if (value && typeof value === 'object' && !Array.isArray(value) && typeof value.members === 'string') return value.members;
  return JSON.stringify(value);
}

function credits(fields: Assertion[]): Credit[] {
  const seen = new Map<string, Credit>();
  for (const { citation } of fields) {
    const credit = { sourceId: citation.source_id, href: attributionLinks(citation.attribution)[0] ?? null,
      attribution: citation.attribution, gap: attributionGap(citation) };
    seen.set(JSON.stringify(credit), credit);
  }
  return [...seen.values()];
}

function groupFacts(fields: Assertion[], order: string[]): FactGroup[] {
  const names = [...new Set(fields.map(f => f.field))].sort((a, b) =>
    (order.includes(a) ? order.indexOf(a) : order.length) - (order.includes(b) ? order.indexOf(b) : order.length));
  return names.map(field => {
    const byValue = new Map<string, Assertion[]>();
    for (const f of fields.filter(f => f.field === field)) byValue.set(JSON.stringify(f.value), [...byValue.get(JSON.stringify(f.value)) ?? [], f]);
    return { field, facts: [...byValue.values()].map(same => ({ value: displayValue(same[0]!.value),
      assertionIds: same.map(f => f.assertion_id), credits: credits(same) })) };
  });
}

export function slotLabel(code: string): SlotLabel {
  const parts = code ? code.split('.') : [];
  const kase = CASES.find(([tag]) => tag === parts[0]);
  const words = parts.map((part, i) => i === 0 && kase ? kase[1] : COMPONENTS[part]);
  if (words.some(word => word === undefined)) return { text: code, unknown: true };
  return { text: words.join(', '), unknown: false };
}

function rank(slot: string): number[] {
  return slot.split('.').map(part => ORDER.includes(part) ? ORDER.indexOf(part) : ORDER.length);
}

function paradigmTables(fields: Assertion[]): ParadigmTable[] {
  return [...new Set(fields.map(f => f.citation.source_id))].map(sourceId => {
    const own = fields.filter(f => f.citation.source_id === sourceId);
    const cells = new Map<string, ParadigmCell>();
    for (const f of own) {
      const value = f.value as { slot: string; forms: string[] };
      const cell = cells.get(value.slot) ?? { forms: [], assertionIds: [] };
      cell.forms.push(...value.forms); cell.assertionIds.push(f.assertion_id);
      cells.set(value.slot, cell);
    }
    const caseSlot = (slot: string) => CASES.some(([tag]) => slot === tag || slot.startsWith(`${tag}.`)) && !slotLabel(slot).unknown;
    const rest = (slot: string) => slot.split('.').slice(1).join('.');
    const columnKeys = [...new Set([...cells.keys()].filter(caseSlot).map(rest))].sort((a, b) =>
      (COLUMN_ORDER.includes(a) ? COLUMN_ORDER.indexOf(a) : COLUMN_ORDER.length) - (COLUMN_ORDER.includes(b) ? COLUMN_ORDER.indexOf(b) : COLUMN_ORDER.length));
    const columns = columnKeys.map(key => ({ key, label: key ? slotLabel(key) : { text: 'Number not given in source', unknown: false } }));
    const caseRows = CASES.filter(([tag]) => columnKeys.some(key => cells.has(key ? `${tag}.${key}` : tag)))
      .map(([tag, label]) => ({ label, cells: columnKeys.map(key => cells.get(key ? `${tag}.${key}` : tag) ?? null) }));
    const formRows = [...cells.keys()].filter(slot => !caseSlot(slot)).sort((a, b) => {
      const [x, y] = [rank(a), rank(b)];
      for (let i = 0; i < Math.max(x.length, y.length); i++) if ((x[i] ?? -1) !== (y[i] ?? -1)) return (x[i] ?? -1) - (y[i] ?? -1);
      return a < b ? -1 : a > b ? 1 : 0;
    }).map(slot => ({ slot, label: slotLabel(slot), cell: cells.get(slot)! }));
    return { sourceId, credits: credits(own), assertionIds: own.map(f => f.assertion_id), columns, caseRows, formRows };
  });
}

const isParadigm = (f: Assertion) => f.field === 'paradigm' && f.subject.kind === 'card' && f.value !== null &&
  typeof f.value === 'object' && !Array.isArray(f.value) && typeof f.value.slot === 'string' &&
  Array.isArray(f.value.forms) && f.value.forms.every(form => typeof form === 'string');

/** Readable projection of one source card. Every assertion lands in exactly one fact, sense, table or `other`. */
export function readableEntry(row: ReleaseRow, ordinal: number): ReadableEntry {
  const onCard = (f: Assertion) => f.subject.kind === 'card' && f.subject.id === row.card_id;
  const facts = groupFacts(row.fields.filter(f => onCard(f) && CARD_FACTS.includes(f.field)), CARD_FACTS);
  const senseIds = [...new Set(row.fields.filter(f => f.subject.kind === 'sense').map(f => f.subject.id))];
  const senses = senseIds.map(id => ({ id, groups: groupFacts(row.fields.filter(f => f.subject.kind === 'sense' && f.subject.id === id), SENSE_FACTS) }));
  const paradigms = paradigmTables(row.fields.filter(f => onCard(f) && isParadigm(f)));
  const other = groupFacts(row.fields.filter(f => f.subject.kind === 'link' || (onCard(f) ? !CARD_FACTS.includes(f.field) && !isParadigm(f) : f.subject.kind === 'card')), []);
  const named = (field: string) => facts.find(group => group.field === field)?.facts ?? [];
  const display = named(row.card_kind === 'mwe' ? 'mwe_form' : 'spelling')[0]?.value ?? row.card_id;
  const stress = named('stress');
  return { row, ordinal, proper: row.card_kind === 'proper_name', display,
    heading: stress.length === 1 ? stress[0]!.value : display, facts, senses, paradigms, other };
}

/**
 * Group release rows into learner pages by case-insensitive spelling. Common entries keep release order and come
 * first; proper-name entries follow. A page with only proper-name entries is not listed. Rows without one valid
 * key are recorded as unlisted refusals, never guessed from locators.
 */
export function groupReleasePages(rows: ReleaseRow[]): { pages: ReleasePageGroup[]; dispositions: Disposition[] } {
  const byKey = new Map<string, ReleaseRow[]>();
  const refused: Disposition[] = [];
  for (const row of rows) {
    try { const key = pageKey(row); byKey.set(key, [...byKey.get(key) ?? [], row]); }
    catch (error) {
      if (!(error instanceof PageKeyError)) throw error;
      refused.push({ cardId: row.card_id, cardKind: row.card_kind, key: null, ordinal: null, listed: false, reason: error.message });
    }
  }
  const collator = new Intl.Collator('uk');
  const pages = [...byKey.entries()].filter(([, group]) => group.some(row => row.card_kind !== 'proper_name'))
    .sort(([a], [b]) => collator.compare(a, b) || (a < b ? -1 : a > b ? 1 : 0))
    .map(([key, group]) => {
      const ordered = [...group.filter(row => row.card_kind !== 'proper_name'), ...group.filter(row => row.card_kind === 'proper_name')];
      const entries = ordered.map((row, i) => readableEntry(row, i + 1));
      return { key, entries, title: [...new Set(entries.filter(e => !e.proper).map(e => e.display))].join(' / ') };
    });
  const listed = new Map(pages.flatMap(page => page.entries.map(entry => [entry.row.card_id, [page.key, entry.ordinal] as const])));
  const dispositions = rows.map(row => {
    const done = refused.find(d => d.cardId === row.card_id);
    if (done) return done;
    const place = listed.get(row.card_id);
    return place ? { cardId: row.card_id, cardKind: row.card_kind, key: place[0], ordinal: place[1], listed: true, reason: 'Listed entry' } :
      { cardId: row.card_id, cardKind: row.card_kind, key: pageKey(row), ordinal: null, listed: false, reason: 'Proper name without a common entry on its page' };
  });
  return { pages, dispositions };
}

export const pagePath = (key: string, compare = false) => `/lexicon-v2/${compare ? 'compare/' : ''}word/${encodeURIComponent(key)}/`;
