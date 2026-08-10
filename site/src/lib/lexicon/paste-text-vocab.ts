/**
 * Paste-text deck builder — pure extraction & attestation classification (#5882).
 *
 * The Atlas search index is VESUM-gated (every entry passes VESUM attestation
 * before publication — see `docs/best-practices/audit-standards.md`), so it
 * doubles as a client-side attestation source with zero extra bundle cost.
 * A pasted word is "atlas_attested" only when it resolves to a real Atlas
 * row; everything else is "unverified" and deselected by default so no
 * unattested string is ever silently treated as confirmed vocabulary. CEFR is
 * optional guidance: an attested row with a real learner gloss remains
 * selectable even when no CEFR level is published, without inventing one.
 *
 * #5882 residual (Fable GO SHARDED-EXACT): a form absent from the Atlas index
 * can still be a REAL Ukrainian word form the MVP simply doesn't know about
 * yet — VESUM (`site/src/lib/lexicon/vesum-form-shard.ts`) covers 6.7M forms.
 * Classification order: (1) direct Atlas hit; (2) fold-up — the form is a
 * VESUM-known inflection of an Atlas-attested lemma, and UNAMBIGUOUSLY so
 * (exactly one distinct Atlas row reachable through the VESUM lemma
 * candidates) — treated as attested via the lemma's own Atlas row; (3)
 * `vesum_form` — VESUM knows the form but either no candidate lemma is
 * Atlas-attested, or ≥2 distinct Atlas rows are reachable (a true homograph:
 * folding would silently guess which word the learner meant); (4)
 * `unverified` — VESUM has no record of the form at all, OR its shard fetch
 * degraded (network/host failure). `vesum_form` is never save-eligible in
 * this PR (see `isSaveEligiblePasteCandidate`) — it is a transparency signal
 * ("this is a real word form"), not a confirmed dictionary entry.
 */

import { CEFR_LEVELS, parseCefrLevel, type CefrLevel } from './levels';
import { vesumFormKey, type VesumFormResult } from './vesum-form-key';

export type PasteCandidateStatus = 'atlas_attested' | 'vesum_form' | 'unverified';

/** Minimal shape this module needs from a search-index row (see search.ts SearchRow). */
export interface AtlasAttestationRow {
  l: string;
  s: string;
  g: string | null;
  c?: string;
}

export interface PasteCandidate {
  text: string;
  cefr: CefrLevel | null;
  status: PasteCandidateStatus;
  atlasSlug: string | null;
  gloss: string | null;
  selected: boolean;
  /** Distinct lemmas VESUM records for this form when status is
   * 'vesum_form' (informational only — never a save-eligibility signal).
   * Null for every other status. */
  vesumLemmas: readonly string[] | null;
  /** True when a VESUM shard fetch failed for this form — classification
   * fell back to the MVP-only 'unverified' path instead of a real VESUM
   * miss (binding design point 6: lose recall, never precision). */
  degraded: boolean;
}

export interface PasteCandidateCounts {
  total: number;
  selected: number;
  attested: number;
  vesumForm: number;
  unverified: number;
  /** Count of candidates whose VESUM shard fetch failed — surfaced as a
   * user-visible degradation notice, distinct from a real VESUM miss. */
  degraded: number;
  byLevel: Record<CefrLevel, number>;
}

/** Index Atlas rows by lemma and slug (lowercased) for O(1) attestation lookup. */
export function buildAtlasAttestationIndex(
  rows: readonly AtlasAttestationRow[],
): Map<string, AtlasAttestationRow> {
  const index = new Map<string, AtlasAttestationRow>();
  for (const row of rows) {
    if (row.l) index.set(row.l.toLocaleLowerCase(), row);
    if (row.s) index.set(row.s.toLocaleLowerCase(), row);
  }
  return index;
}

function cleanGloss(gloss: string | null): string | null {
  if (!gloss) return null;
  const trimmed = gloss.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function attestedCandidateFromRow(text: string, row: AtlasAttestationRow): PasteCandidate {
  const cefr = parseCefrLevel(row.c);
  const gloss = cleanGloss(row.g);
  return {
    text,
    cefr,
    status: 'atlas_attested',
    atlasSlug: row.s,
    gloss,
    // Missing CEFR is still eligible guidance-wise when the row has a real
    // gloss; preserve the legacy attested selection for rows with CEFR.
    selected: cefr !== null || gloss !== null,
    vesumLemmas: null,
    degraded: false,
  };
}

/**
 * Classify pasted-text candidate words against the Atlas attestation index,
 * with an optional VESUM form-shard fold-up pass (#5882 residual). No
 * candidate is ever assigned an invented CEFR level or gloss: both are
 * `null` unless a real Atlas row backs them, whether reached directly or via
 * an unambiguous VESUM fold.
 *
 * `vesumResults` is keyed by `vesumFormKey(word)` — pre-resolved by
 * `VesumFormShardClient.resolve()` (`vesum-form-shard.ts`) before calling
 * this pure function. Omitting it (or a form missing from the map) is
 * equivalent to VESUM being fully unavailable: those forms classify exactly
 * as the pre-#5882-residual MVP did.
 */
export function classifyPasteCandidates(
  lemmaKeys: readonly string[],
  attestationIndex: ReadonlyMap<string, AtlasAttestationRow>,
  vesumResults?: ReadonlyMap<string, VesumFormResult>,
): PasteCandidate[] {
  return lemmaKeys.map((text) => {
    const directRow = attestationIndex.get(text.toLocaleLowerCase());
    if (directRow) return attestedCandidateFromRow(text, directRow);

    const vesumResult = vesumResults?.get(vesumFormKey(text));
    if (!vesumResult || vesumResult.lemmas.length === 0) {
      return {
        text,
        cefr: null,
        status: 'unverified',
        atlasSlug: null,
        gloss: null,
        selected: false,
        vesumLemmas: null,
        degraded: vesumResult?.degraded ?? false,
      };
    }

    // Fold-up: unambiguous only when exactly one DISTINCT Atlas row is
    // reachable through the VESUM lemma candidates. ≥2 distinct rows is a
    // true homograph (binding design point 5) — never auto-fold, because
    // folding the wrong lemma would silently misattest a word the learner
    // never actually saw confirmed.
    const reachableRows = new Map<string, AtlasAttestationRow>();
    for (const lemma of vesumResult.lemmas) {
      const row = attestationIndex.get(lemma.toLocaleLowerCase());
      if (row) reachableRows.set(row.s, row);
    }

    if (reachableRows.size === 1) {
      const [row] = reachableRows.values();
      return attestedCandidateFromRow(text, row);
    }

    return {
      text,
      cefr: null,
      status: 'vesum_form',
      atlasSlug: null,
      gloss: null,
      selected: false,
      vesumLemmas: vesumResult.lemmas,
      degraded: false,
    };
  });
}

/**
 * A candidate is safe to persist into a saved deck only when it resolves to a
 * real Atlas row. A missing-CEFR row additionally needs a real learner gloss so
 * it is displayable without a level fallback; known-CEFR rows retain the
 * existing attested path. CEFR remains nullable and no downstream fallback may
 * invent a level just because a bulk toggle or stray click left `selected` true.
 */
export function isSaveEligiblePasteCandidate(candidate: PasteCandidate): boolean {
  return candidate.status === 'atlas_attested' &&
    (candidate.cefr !== null || candidate.gloss !== null);
}

/**
 * The fail-closed save set: candidates the user selected AND that are
 * save-eligible. This is the final gate before a paste-text deck is
 * persisted — the authoritative check regardless of how `selected` got set.
 */
export function selectSaveEligiblePasteCandidates(
  candidates: readonly PasteCandidate[],
): PasteCandidate[] {
  return candidates.filter((c) => c.selected && isSaveEligiblePasteCandidate(c));
}

/** Tally selection/attestation/CEFR counts for the wizard's review step. */
export function summarizePasteCandidates(
  candidates: readonly PasteCandidate[],
): PasteCandidateCounts {
  const byLevel = Object.fromEntries(CEFR_LEVELS.map((level) => [level, 0])) as Record<
    CefrLevel,
    number
  >;
  let selected = 0;
  let attested = 0;
  let vesumForm = 0;
  let unverified = 0;
  let degraded = 0;

  for (const candidate of candidates) {
    if (candidate.status === 'atlas_attested') attested++;
    else if (candidate.status === 'vesum_form') vesumForm++;
    else unverified++;

    if (candidate.degraded) degraded++;

    if (candidate.selected) {
      selected++;
      if (candidate.cefr) byLevel[candidate.cefr]++;
    }
  }

  return { total: candidates.length, selected, attested, vesumForm, unverified, degraded, byLevel };
}
