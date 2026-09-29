/**
 * Teacher-table deck artifacts (#8843, epic #4387) — types, lazy loader and lookups.
 *
 * Contract: docs/practice/teacher-deck-artifacts.md. The generator is
 * scripts/lexicon/teacher_deck_shard.py; `npm run hydrate` serves the pinned files
 * as `<shardBaseUrl>/practice-deck.teacher.json` and `practice-cloze.teacher.json`.
 * The practice page fetches them only when the deck is selected.
 */

import type {
  PracticeClassifyItem,
  PracticeClozeItem,
  PracticeParadigmItem,
  PracticeStressItem,
  PracticeSynonymItem,
} from './srs';

export const TEACHER_DECK_SCHEMA = 'atlas-practice-teacher-deck';
export const TEACHER_CLOZE_SCHEMA = 'atlas-practice-teacher-cloze';
export const TEACHER_DECK_SCHEMA_VERSION = 1;

export const TEACHER_CARD_KINDS = ['recognition', 'production', 'cloze', 'grammar'] as const;
export type TeacherCardKind = (typeof TEACHER_CARD_KINDS)[number];
export type TeacherGrammarMode = 'stress' | 'paradigm' | 'classify' | 'synonym' | 'antonym';

export interface TeacherChoiceOption {
  entryId: string;
  label: string;
  kind: 'answer' | 'distractor';
}

export interface TeacherChoiceItem {
  choiceId: string;
  direction: 'uk-en' | 'en-uk';
  prompt: string;
  options: TeacherChoiceOption[];
}

export interface TeacherAspect {
  value: 'imperf' | 'perf' | 'dual' | 'unknown';
  basis: string;
  lemma?: string | null;
}

export interface TeacherDeckCards {
  recognition: { cardId: string; choice: TeacherChoiceItem | null };
  production: { cardId: string; choice: TeacherChoiceItem | null } | null;
  cloze: { cardId: string; clozeIds: string[] } | null;
  grammar: { cardId: string; items: { mode: TeacherGrammarMode; id: string }[] } | null;
}

export interface TeacherDeckEntry {
  entryId: string;
  key: string;
  uk: string;
  /** Learner-facing English: the teacher's English with the source aspect label. */
  en: string;
  /** The teacher's English verbatim. */
  teacherEn: string;
  aspect: TeacherAspect | null;
  /** Order key; newest = highest. */
  firstSeen: number;
  multiword: boolean;
  sourceRows?: number[];
  sourceKeys?: string[];
  atlas: { slug: string; pos?: string | null; identityConflict?: boolean } | null;
  conflicts: string[];
  aspectPartners?: string[];
  matching: boolean;
  cards: TeacherDeckCards;
}

type Tagged = { entryId: string; cardId: string };
export type TeacherStressItem = PracticeStressItem & Tagged;
export type TeacherParadigmItem = PracticeParadigmItem & Tagged;
export type TeacherClassifyItem = PracticeClassifyItem & Tagged;
export type TeacherSynonymItem = PracticeSynonymItem & Tagged;

export interface TeacherClozeItem extends PracticeClozeItem {
  entryId: string;
  cardId: string;
  source?: 'teacher-lesson' | 'textbook';
}

export interface TeacherDeckFile {
  schema: typeof TEACHER_DECK_SCHEMA;
  schemaVersion: number;
  deckId: string;
  deckVersion: string;
  entries: TeacherDeckEntry[];
  stress?: TeacherStressItem[];
  paradigm?: TeacherParadigmItem[];
  classify?: TeacherClassifyItem[];
  synonym?: TeacherSynonymItem[];
}

export interface TeacherClozeFile {
  schema: typeof TEACHER_CLOZE_SCHEMA;
  schemaVersion: number;
  deckId: string;
  deckVersion: string;
  cloze: TeacherClozeItem[];
}

export type TeacherGrammarItem =
  | { mode: 'stress'; item: TeacherStressItem }
  | { mode: 'paradigm'; item: TeacherParadigmItem }
  | { mode: 'classify'; item: TeacherClassifyItem }
  | { mode: 'synonym' | 'antonym'; item: TeacherSynonymItem };

/** A loaded deck with its lookups. Built once per fetched deck version. */
export interface TeacherDeck {
  deckId: string;
  deckVersion: string;
  entries: TeacherDeckEntry[];
  entriesById: ReadonlyMap<string, TeacherDeckEntry>;
  clozeById: ReadonlyMap<string, TeacherClozeItem>;
  grammarById: ReadonlyMap<string, TeacherGrammarItem>;
}

/** Deck-data config carried by a virtual deck that practises from served artifacts. */
export interface ArtifactDeckPracticeConfig {
  deckFile: string;
  clozeFile: string;
  /** Default new words introduced per local day (zero allowed). */
  newPerDay: number;
  /** Default review cap per local day. */
  reviewCap: number;
}

export class TeacherDeckLoadError extends Error {}

function assertFile(
  payload: unknown,
  schema: string,
  deckId: string,
  name: string,
): asserts payload is { schema: string; schemaVersion: number; deckId: string; deckVersion: string } {
  const record = payload as Record<string, unknown> | null;
  if (!record || typeof record !== 'object') throw new TeacherDeckLoadError(`${name}: not a JSON object`);
  if (record.schema !== schema || record.schemaVersion !== TEACHER_DECK_SCHEMA_VERSION) {
    throw new TeacherDeckLoadError(`${name}: unexpected schema ${String(record.schema)} v${String(record.schemaVersion)}`);
  }
  if (record.deckId !== deckId) throw new TeacherDeckLoadError(`${name}: deck id ${String(record.deckId)} != ${deckId}`);
  if (typeof record.deckVersion !== 'string' || !record.deckVersion) {
    throw new TeacherDeckLoadError(`${name}: missing deckVersion`);
  }
}

/**
 * Validate the two served files and index them. The deck and the cloze file must
 * carry the same `deckVersion` (they are published together).
 */
export function buildTeacherDeck(deckId: string, deckPayload: unknown, clozePayload: unknown): TeacherDeck {
  assertFile(deckPayload, TEACHER_DECK_SCHEMA, deckId, 'teacher deck');
  assertFile(clozePayload, TEACHER_CLOZE_SCHEMA, deckId, 'teacher cloze');
  const deckFile = deckPayload as unknown as TeacherDeckFile;
  const clozeFile = clozePayload as unknown as TeacherClozeFile;
  if (deckFile.deckVersion !== clozeFile.deckVersion) {
    throw new TeacherDeckLoadError(
      `teacher deck version ${deckFile.deckVersion} != cloze version ${clozeFile.deckVersion}`,
    );
  }
  if (!Array.isArray(deckFile.entries)) throw new TeacherDeckLoadError('teacher deck: entries missing');

  const entriesById = new Map<string, TeacherDeckEntry>();
  for (const entry of deckFile.entries) entriesById.set(entry.entryId, entry);
  const clozeById = new Map<string, TeacherClozeItem>();
  for (const item of clozeFile.cloze ?? []) clozeById.set(item.clozeId, item);
  const grammarById = new Map<string, TeacherGrammarItem>();
  for (const item of deckFile.stress ?? []) grammarById.set(item.stressId, { mode: 'stress', item });
  for (const item of deckFile.paradigm ?? []) grammarById.set(item.paradigmId, { mode: 'paradigm', item });
  for (const item of deckFile.classify ?? []) grammarById.set(item.classifyId, { mode: 'classify', item });
  for (const item of deckFile.synonym ?? []) {
    grammarById.set(item.synonymId, { mode: item.polarity === 'antonym' ? 'antonym' : 'synonym', item });
  }
  return {
    deckId,
    deckVersion: deckFile.deckVersion,
    entries: deckFile.entries,
    entriesById,
    clozeById,
    grammarById,
  };
}

export type JsonFetcher = (url: string) => Promise<unknown>;

/** Fetch both served files (in parallel) and build the deck. Any failure throws. */
export async function loadTeacherDeck(
  deckId: string,
  config: Pick<ArtifactDeckPracticeConfig, 'deckFile' | 'clozeFile'>,
  shardBaseUrl: string,
  fetchJson: JsonFetcher,
): Promise<TeacherDeck> {
  const base = shardBaseUrl.replace(/\/$/, '');
  const [deckPayload, clozePayload] = await Promise.all([
    fetchJson(`${base}/${config.deckFile}`),
    fetchJson(`${base}/${config.clozeFile}`),
  ]);
  return buildTeacherDeck(deckId, deckPayload, clozePayload);
}

/** Card ids the entry actually has, in contract order. */
export function entryCardKinds(entry: TeacherDeckEntry): TeacherCardKind[] {
  return TEACHER_CARD_KINDS.filter((kind) => entry.cards[kind] !== null && entry.cards[kind] !== undefined);
}

export function entryCardId(entry: TeacherDeckEntry, kind: TeacherCardKind): string | null {
  return entry.cards[kind]?.cardId ?? null;
}

/** Cloze ids of the entry that resolve in the loaded cloze file. */
export function entryClozeItems(deck: TeacherDeck, entry: TeacherDeckEntry): TeacherClozeItem[] {
  return (entry.cards.cloze?.clozeIds ?? [])
    .map((id) => deck.clozeById.get(id))
    .filter((item): item is TeacherClozeItem => Boolean(item));
}

/** Grammar items of the entry that resolve in the deck, in the deck's order. */
export function entryGrammarItems(deck: TeacherDeck, entry: TeacherDeckEntry): TeacherGrammarItem[] {
  return (entry.cards.grammar?.items ?? [])
    .map((ref) => deck.grammarById.get(ref.id))
    .filter((item): item is TeacherGrammarItem => Boolean(item));
}

/** Per-kind card counts for the deck overview (kinds with zero cards are omitted by callers). */
export function teacherDeckCardCounts(deck: TeacherDeck): Record<TeacherCardKind, number> {
  const counts: Record<TeacherCardKind, number> = { recognition: 0, production: 0, cloze: 0, grammar: 0 };
  for (const entry of deck.entries) {
    for (const kind of entryCardKinds(entry)) counts[kind] += 1;
  }
  return counts;
}
