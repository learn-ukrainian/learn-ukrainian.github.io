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
  PracticeImperativeItem,
  PracticeParadigmItem,
  PracticeParonymItem,
  PracticeStressItem,
  PracticeSynonymItem,
} from "./srs";
import { isPracticeModeEnabled } from "./srs";
import practiceDeckPointer from "../../data/lexicon-practice-deck.pointer.json";
import {
  displayGloss,
  resolveHeritageBoxes,
  type LexiconEntryForSeverity,
} from "./heritage-severity";

/** Optional Atlas evidence stays optional: legacy practice shards carry only provenance. */
type PracticeDisplayEntry = LexiconEntryForSeverity & {
  lemma: string;
  gloss: string;
  glossClean?: string;
  heritage?: string | null;
};

export function practiceHeritageBoxes(entry: PracticeDisplayEntry) {
  const raw = entry.heritage?.toLowerCase();
  const classification = raw === "borrowed" || raw === "loanword" ? "borrowing"
    : raw === "avoid" ? "russianism" : raw;
  return resolveHeritageBoxes({
    ...entry,
    heritage_status: entry.heritage_status ?? { classification },
  });
}

/** Display only; never rewrite the shard, eligibility inputs or saved progress. */
export function practiceDisplayGloss(entry: PracticeDisplayEntry, concise = false): string {
  const label = practiceHeritageBoxes(entry).usageLabel;
  const full = displayGloss(entry.gloss, label);
  // Qualify the complete clause before reading glossClean: legacy first-sense
  // truncation can leave an opening parenthesis and half of a norm claim.
  if (!concise || full?.note) return full?.text ?? "";
  const clean = entry.glossClean?.trim() || entry.gloss.split(/[;,]/, 1)[0].replace(/\s+/g, " ").trim();
  return displayGloss(clean, label)?.text ?? "";
}

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
  "imperative",
] as const;

export type PracticeDrillKind = (typeof PRACTICE_DRILL_KINDS)[number];

export const PUBLISHED_PRACTICE_SHARDS: ReadonlySet<string> = new Set(
  Array.isArray(practiceDeckPointer?.files)
    ? practiceDeckPointer.files.map((f: { path: string }) => f.path)
    : [],
);

let overridePublishedShards: ReadonlySet<string> | null = null;

export function setPublishedPracticeShardsForTesting(
  shards: ReadonlySet<string> | null,
): void {
  overridePublishedShards = shards;
}

export function isPracticeShardPublished(
  filename: string,
  publishedShards: ReadonlySet<string> = overridePublishedShards ?? PUBLISHED_PRACTICE_SHARDS,
): boolean {
  return publishedShards.has(filename);
}

export type PracticeDrillFields = {
  cloze: PracticeClozeItem[];
  stress: PracticeStressItem[];
  classify: PracticeClassifyItem[];
  paradigm: PracticeParadigmItem[];
  synonym: PracticeSynonymItem[];
  paronym: PracticeParonymItem[];
  heritage: PracticeHeritageItem[];
  antonym: PracticeAntonymItem[];
  imperative: PracticeImperativeItem[];
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

export function practiceDrillShardUrls(
  shardBaseUrl: string,
  level: string,
  publishedOnly = false,
  publishedShards: ReadonlySet<string> = overridePublishedShards ?? PUBLISHED_PRACTICE_SHARDS,
): string[] {
  return PRACTICE_DRILL_KINDS
    .filter((kind) => isPracticeModeEnabled(kind) && (!publishedOnly || isPracticeShardPublished(`practice-${kind}.${level}.json`, publishedShards)))
    .map((kind) => `${shardBaseUrl}/practice-${kind}.${level}.json`);
}

function itemsFromShard<T>(payload: unknown, key: PracticeDrillKind): T[] {
  return ((payload as Record<string, T[] | undefined> | null)?.[key] ?? []) as T[];
}

export function drillFieldsFromShardResults(results: Partial<Record<PracticeDrillKind, unknown>>): PracticeDrillFields {
  return {
    cloze: itemsFromShard<PracticeClozeItem>(results.cloze, "cloze"),
    stress: itemsFromShard<PracticeStressItem>(results.stress, "stress"),
    classify: itemsFromShard<PracticeClassifyItem>(results.classify, "classify"),
    paradigm: itemsFromShard<PracticeParadigmItem>(results.paradigm, "paradigm"),
    synonym: isPracticeModeEnabled('synonym') ? itemsFromShard<PracticeSynonymItem>(results.synonym, "synonym") : [],
    paronym: itemsFromShard<PracticeParonymItem>(results.paronym, "paronym"),
    heritage: itemsFromShard<PracticeHeritageItem>(results.heritage, "heritage"),
    antonym: itemsFromShard<PracticeAntonymItem>(results.antonym, "antonym"),
    imperative: itemsFromShard<PracticeImperativeItem>(results.imperative, "imperative"),
  };
}

export async function fetchPracticeDrillFields(
  shardBaseUrl: string,
  level: string,
  cache: ShardJsonCache,
  publishedShards: ReadonlySet<string> = overridePublishedShards ?? PUBLISHED_PRACTICE_SHARDS,
): Promise<PracticeDrillFields> {
  const results = await Promise.all(
    PRACTICE_DRILL_KINDS.map(async (kind) => {
      if (!isPracticeModeEnabled(kind)) return [kind, {}] as const;
      const filename = `practice-${kind}.${level}.json`;
      if (!isPracticeShardPublished(filename, publishedShards)) {
        return [kind, {}] as const;
      }
      const url = `${shardBaseUrl}/${filename}`;
      return [kind, await getShardJson<unknown>(url, cache).catch(softSkipUnpublishedDrillShard)] as const;
    }),
  );
  return drillFieldsFromShardResults(Object.fromEntries(results));
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
    imperative: batches.flatMap((batch) => batch.imperative),
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
    synonym: isPracticeModeEnabled('synonym') ? [...(deck.synonym ?? []), ...fields.synonym] : [],
    paronym: [...(deck.paronym ?? []), ...fields.paronym],
    heritage: [...(deck.heritage ?? []), ...fields.heritage],
    antonym: [...(withAntonym.antonym ?? []), ...fields.antonym],
    imperative: [...(deck.imperative ?? []), ...fields.imperative],
  };
  return merged;
}
