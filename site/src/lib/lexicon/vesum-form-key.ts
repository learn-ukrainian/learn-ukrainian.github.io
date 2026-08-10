/**
 * VESUM form-key normalization + hash-shard id (TypeScript side of the dual
 * contract) — #5882 residual form-level VESUM attestation, Fable GO
 * SHARDED-EXACT design.
 *
 * Must stay byte-compatible with `scripts/lexicon/vesum_form_key.py`. Both
 * sides need the SAME key (so a form hashes to the SAME shard client-side as
 * it was written server-side) and the SAME hash (so the shard id math
 * agrees). Parity is golden-tested via `vesum_form_key_vectors.json` — both
 * languages consume the identical vector file (see
 * `tests/test_generate_vesum_form_shards.py` and
 * `site/tests/unit/vesum-form-shard.test.ts`).
 */
import { normalizeAtlasText } from './normalize';

// VESUM's own data uses U+02BC (ʼ, MODIFIER LETTER APOSTROPHE) as the
// Ukrainian orthographic apostrophe. Pasted learner text commonly carries a
// typewriter apostrophe (U+0027) or a curly quote (U+2019, occasionally
// U+02BB) instead. Folding these variants to the canonical codepoint before
// hashing only ever WIDENS a match (never invents a wrong one — the rest of
// the key still has to agree), so it is a safe recall improvement.
const APOSTROPHE_VARIANTS_RE = /['’ʻ]/g;
const CANONICAL_APOSTROPHE = 'ʼ';

/** Normalize a word to its VESUM form-shard lookup key. */
export function vesumFormKey(value: string): string {
  return normalizeAtlasText(value).replace(APOSTROPHE_VARIANTS_RE, CANONICAL_APOSTROPHE);
}

export const VESUM_FORM_SHARD_COUNT = 4096;

const FNV_OFFSET_BASIS = 0x811c9dc5;
const FNV_PRIME = 0x01000193;

/**
 * FNV-1a 32-bit hash over the UTF-8 bytes of `value`. Deterministic,
 * dependency-free, and byte-identical to the Python twin
 * (`scripts/lexicon/vesum_form_key.py::fnv1a32`, which does the same
 * wrapping 32-bit multiply via `& 0xFFFFFFFF`; `Math.imul` gives the
 * identical wrapping semantics here).
 */
export function fnv1a32(value: string): number {
  const bytes = new TextEncoder().encode(value);
  let hash = FNV_OFFSET_BASIS;
  for (let i = 0; i < bytes.length; i++) {
    hash ^= bytes[i];
    hash = Math.imul(hash, FNV_PRIME) >>> 0;
  }
  return hash >>> 0;
}

/**
 * Shard id for an already-normalized form key — a zero-padded 3-digit hex
 * string regardless of `shardCount` (so the width never has to be
 * negotiated between the generator and the client).
 */
export function vesumShardId(formKey: string, shardCount = VESUM_FORM_SHARD_COUNT): string {
  return (fnv1a32(formKey) % shardCount).toString(16).padStart(3, '0');
}

/**
 * A single form's VESUM lookup outcome. `degraded` marks a shard-fetch
 * failure — `lemmas` is unreliable in that case and callers MUST treat it
 * as unverified, never as a confirmed VESUM miss (binding design point 6:
 * lose recall, never precision).
 */
export interface VesumFormResult {
  /** Distinct lemmas VESUM records for this form; empty = not in VESUM. */
  lemmas: readonly string[];
  degraded: boolean;
}
