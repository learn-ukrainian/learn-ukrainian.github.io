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
 */

import { CEFR_LEVELS, parseCefrLevel, type CefrLevel } from './levels';

export type PasteCandidateStatus = 'atlas_attested' | 'unverified';

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
}

export interface PasteCandidateCounts {
  total: number;
  selected: number;
  attested: number;
  unverified: number;
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

/**
 * Classify pasted-text candidate words against the Atlas attestation index.
 * No candidate is ever assigned an invented CEFR level or gloss: both are
 * `null` unless a real Atlas row backs them.
 */
export function classifyPasteCandidates(
  lemmaKeys: readonly string[],
  attestationIndex: ReadonlyMap<string, AtlasAttestationRow>,
): PasteCandidate[] {
  return lemmaKeys.map((text) => {
    const row = attestationIndex.get(text.toLocaleLowerCase());
    if (row) {
      const cefr = parseCefrLevel(row.c);
      return {
        text,
        cefr,
        status: 'atlas_attested',
        atlasSlug: row.s,
        gloss: cleanGloss(row.g),
        // Missing CEFR is still eligible guidance-wise when the row has a real
        // gloss; preserve the legacy attested selection for rows with CEFR.
        selected: cefr !== null || cleanGloss(row.g) !== null,
      };
    }
    return {
      text,
      cefr: null,
      status: 'unverified',
      atlasSlug: null,
      gloss: null,
      selected: false,
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
  let unverified = 0;

  for (const candidate of candidates) {
    if (candidate.status === 'atlas_attested') attested++;
    else unverified++;

    if (candidate.selected) {
      selected++;
      if (candidate.cefr) byLevel[candidate.cefr]++;
    }
  }

  return { total: candidates.length, selected, attested, unverified, byLevel };
}
