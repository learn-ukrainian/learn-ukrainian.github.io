/**
 * Deduped practice/Atlas JSON fetch plus optional drill-kind hydration.
 *
 * HTTP 404 on a drill shard means "not published for this level" and may be
 * treated as an empty payload. Network faults and 5xx must surface (#6768).
 */

import type {
  PracticeAntonymItem,
  PracticeClassifyItem,
  PracticeClozeItem,
  PracticeDeckData,
  PracticeHeritageItem,
  PracticeParadigmItem,
  PracticeParonymItem,
  PracticeStressItem,
  PracticeSynonymItem,
} from "./srs";

export type ShardJsonCache = Map<string, Promise<unknown>>;

export const PRACTICE_DRILL_KINDS = [
  "cloze",
  "stress",
  "classify",
  "paradigm",
  "synonym",
  "paronym",
  "heritage",
  "antonym",
] as const;

export type PracticeDrillKind = (typeof PRACTICE_DRILL_KINDS)[number];

export type PracticeDrillFields = {
  cloze: PracticeClozeItem[];
  stress: PracticeStressItem[];
  classify: PracticeClassifyItem[];
  paradigm: PracticeParadigmItem[];
  synonym: PracticeSynonymItem[];
  paronym: PracticeParonymItem[];
  heritage: PracticeHeritageItem[];
  antonym: PracticeAntonymItem[];
};

/** Deduped fetch for practice and Atlas JSON by URL. Concurrent or repeated callers share the promise. */
export async function getShardJson<T>(url: string, cache: ShardJsonCache): Promise<T> {
  let p = cache.get(url) as Promise<T> | undefined;
  if (!p) {
    p = fetch(url).then((res) => {
      if (!res.ok) {
        // Tag the HTTP status so callers can tell an unpublished shard (404,
        // soft-skippable) from a real load fault (network / server error).
        const err = new Error(`Shard fetch failed: ${url}`) as Error & { status?: number };
        err.status = res.status;
        throw err;
      }
      return res.json() as Promise<T>;
    });
    // On failure allow retry next time
    p = p.catch((err) => {
      cache.delete(url);
      throw err;
    });
    cache.set(url, p);
  }
  return p;
}

/**
 * Optional drill-kind shards (and some Atlas search fallbacks) are unpublished
 * per level/type: HTTP 404 means "not shipped", so callers may treat that as an
 * empty payload. Network faults and 5xx must not be rewritten as empty decks
 * (#6768) — rethrow so the Practice load-error path can surface.
 */
export function isMissingShard(reason: unknown): boolean {
  return (reason as { status?: number } | null)?.status === 404;
}

export function softSkipUnpublishedDrillShard(reason: unknown): Record<string, never> {
  if (isMissingShard(reason)) return {};
  throw reason;
}

export function practiceDrillShardUrls(shardBaseUrl: string, level: string): string[] {
  return PRACTICE_DRILL_KINDS.map((kind) => `${shardBaseUrl}/practice-${kind}.${level}.json`);
}

function itemsFromShard<T>(payload: unknown, key: PracticeDrillKind): T[] {
  return ((payload as Record<string, T[] | undefined> | null)?.[key] ?? []) as T[];
}

export function drillFieldsFromShardResults(results: readonly unknown[]): PracticeDrillFields {
  return {
    cloze: itemsFromShard<PracticeClozeItem>(results[0], "cloze"),
    stress: itemsFromShard<PracticeStressItem>(results[1], "stress"),
    classify: itemsFromShard<PracticeClassifyItem>(results[2], "classify"),
    paradigm: itemsFromShard<PracticeParadigmItem>(results[3], "paradigm"),
    synonym: itemsFromShard<PracticeSynonymItem>(results[4], "synonym"),
    paronym: itemsFromShard<PracticeParonymItem>(results[5], "paronym"),
    heritage: itemsFromShard<PracticeHeritageItem>(results[6], "heritage"),
    antonym: itemsFromShard<PracticeAntonymItem>(results[7], "antonym"),
  };
}

export async function fetchPracticeDrillFields(
  shardBaseUrl: string,
  level: string,
  cache: ShardJsonCache,
): Promise<PracticeDrillFields> {
  const results = await Promise.all(
    practiceDrillShardUrls(shardBaseUrl, level).map((url) =>
      getShardJson<unknown>(url, cache).catch(softSkipUnpublishedDrillShard),
    ),
  );
  return drillFieldsFromShardResults(results);
}

export function concatDrillFields(batches: readonly PracticeDrillFields[]): PracticeDrillFields {
  return {
    cloze: batches.flatMap((batch) => batch.cloze),
    stress: batches.flatMap((batch) => batch.stress),
    classify: batches.flatMap((batch) => batch.classify),
    paradigm: batches.flatMap((batch) => batch.paradigm),
    synonym: batches.flatMap((batch) => batch.synonym),
    paronym: batches.flatMap((batch) => batch.paronym),
    heritage: batches.flatMap((batch) => batch.heritage),
    antonym: batches.flatMap((batch) => batch.antonym),
  };
}

type DeckWithAntonym = PracticeDeckData & { antonym?: PracticeAntonymItem[] };

export function appendDrillFields(deck: PracticeDeckData, fields: PracticeDrillFields): PracticeDeckData {
  const withAntonym = deck as DeckWithAntonym;
  const merged: DeckWithAntonym = {
    ...deck,
    cloze: [...(deck.cloze ?? []), ...fields.cloze],
    stress: [...(deck.stress ?? []), ...fields.stress],
    classify: [...(deck.classify ?? []), ...fields.classify],
    paradigm: [...(deck.paradigm ?? []), ...fields.paradigm],
    synonym: [...(deck.synonym ?? []), ...fields.synonym],
    paronym: [...(deck.paronym ?? []), ...fields.paronym],
    heritage: [...(deck.heritage ?? []), ...fields.heritage],
    antonym: [...(withAntonym.antonym ?? []), ...fields.antonym],
  };
  return merged;
}
