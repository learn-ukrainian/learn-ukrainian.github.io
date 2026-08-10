/**
 * Client-side VESUM form-shard fetch/cache for paste-text form-level
 * attestation (#5882 residual, Fable GO SHARDED-EXACT design).
 *
 * Each shard is a static JSON file at `{baseUrl}{shardId}.json` mapping a
 * normalized VESUM form key to its distinct lemma(s), written by
 * `scripts/lexicon/generate_vesum_form_shards.py` (~4096 shards; NOT
 * committed to git — see that script's header for the size-budget
 * rationale). This module fetches only the shards a given word batch
 * actually hashes to, caches them for the session, and NEVER throws: any
 * shard fetch failure degrades the affected forms to `{ degraded: true }`
 * instead of failing the whole paste-text classification flow — lose
 * recall, never precision (binding design point 6).
 */
import { vesumFormKey, vesumShardId, VESUM_FORM_SHARD_COUNT, type VesumFormResult } from './vesum-form-key';

/** Matches the practice/search shard hosting convention under `/lexicon/`. */
export const VESUM_FORM_SHARD_BASE_URL = '/lexicon/vesum-forms/';

/** A shard file's contents: normalized form key -> distinct lemmas. */
export type VesumFormShardPayload = Record<string, string[]>;

const DEGRADED_RESULT: VesumFormResult = { lemmas: [], degraded: true };
const NOT_FOUND_RESULT: VesumFormResult = { lemmas: [], degraded: false };

export type VesumFormFetcher = (url: string) => Promise<Response>;

/**
 * Fetches and caches VESUM form shards, resolving a batch of pasted words to
 * their VESUM lemma results. One instance is meant to live for a tab
 * session (or a wizard open) so repeated lookups reuse already-fetched
 * shards.
 */
export class VesumFormShardClient {
  #fetch: VesumFormFetcher;
  #baseUrl: string;
  #shardCache = new Map<string, Promise<VesumFormShardPayload | null>>();

  constructor(
    fetchImpl: VesumFormFetcher = globalThis.fetch.bind(globalThis),
    baseUrl: string = VESUM_FORM_SHARD_BASE_URL,
  ) {
    this.#fetch = fetchImpl;
    this.#baseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
  }

  #loadShard(shardId: string): Promise<VesumFormShardPayload | null> {
    const cached = this.#shardCache.get(shardId);
    if (cached) return cached;
    const promise = (async (): Promise<VesumFormShardPayload | null> => {
      try {
        const response = await this.#fetch(`${this.#baseUrl}${shardId}.json`);
        if (!response.ok) throw new Error(`VESUM shard fetch failed: ${response.status}`);
        return (await response.json()) as VesumFormShardPayload;
      } catch {
        return null; // caller treats this as a degraded lookup, not a VESUM miss
      }
    })();
    this.#shardCache.set(shardId, promise);
    return promise;
  }

  /**
   * Resolve VESUM lemma results for a batch of pasted words, fetching only
   * the distinct shards the batch touches (in parallel). Keys the returned
   * map by `vesumFormKey(word)`, not the raw word.
   */
  async resolve(words: readonly string[]): Promise<Map<string, VesumFormResult>> {
    const results = new Map<string, VesumFormResult>();
    const keysByShard = new Map<string, Set<string>>();
    const seenKeys = new Set<string>();

    for (const word of words) {
      const key = vesumFormKey(word);
      if (seenKeys.has(key)) continue;
      seenKeys.add(key);
      const shardId = vesumShardId(key, VESUM_FORM_SHARD_COUNT);
      let keys = keysByShard.get(shardId);
      if (!keys) {
        keys = new Set();
        keysByShard.set(shardId, keys);
      }
      keys.add(key);
    }

    await Promise.all(
      [...keysByShard.entries()].map(async ([shardId, keys]) => {
        const shard = await this.#loadShard(shardId);
        for (const key of keys) {
          if (!shard) {
            results.set(key, DEGRADED_RESULT);
            continue;
          }
          const lemmas = shard[key];
          results.set(
            key,
            lemmas && lemmas.length > 0 ? { lemmas, degraded: false } : NOT_FOUND_RESULT,
          );
        }
      }),
    );

    return results;
  }
}
