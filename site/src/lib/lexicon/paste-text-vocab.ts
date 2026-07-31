/**
 * Paste-text deck builder — pure extraction & attestation classification (#5882).
 *
 * The Atlas search index is VESUM-gated (every entry passes VESUM attestation
 * before publication — see `docs/best-practices/audit-standards.md`), so it
 * doubles as a client-side attestation source with zero extra bundle cost.
 * A pasted word is "atlas_attested" only when it resolves to a real Atlas
 * row; everything else is "unverified" and deselected by default so no
 * unattested string is ever silently treated as confirmed vocabulary.
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
      return {
        text,
        cefr: parseCefrLevel(row.c),
        status: 'atlas_attested',
        atlasSlug: row.s,
        gloss: cleanGloss(row.g),
        selected: true,
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
