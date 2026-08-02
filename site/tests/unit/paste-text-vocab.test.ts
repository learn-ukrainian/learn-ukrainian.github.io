import { describe, expect, test } from 'vitest';
import {
  buildAtlasAttestationIndex,
  classifyPasteCandidates,
  isSaveEligiblePasteCandidate,
  selectSaveEligiblePasteCandidates,
  summarizePasteCandidates,
  type AtlasAttestationRow,
  type PasteCandidate,
} from '@site/src/lib/lexicon/paste-text-vocab';
import { parsePlainTextWithTranslations } from '@site/src/lib/lexicon/document-importer';

const SAMPLE_ROWS: AtlasAttestationRow[] = [
  { l: 'привіт', s: 'pryvit', g: 'hello', c: 'A1' },
  { l: 'книжка', s: 'knyzhka', g: 'book', c: 'A2' },
  { l: 'ґудзик', s: 'gudzyk', g: 'button', c: undefined },
  { l: 'абракадабра', s: 'abrakadabra-slug', g: null, c: undefined },
];

describe('buildAtlasAttestationIndex', () => {
  test('indexes rows by lowercased lemma and slug', () => {
    const index = buildAtlasAttestationIndex(SAMPLE_ROWS);
    expect(index.get('привіт')).toBe(SAMPLE_ROWS[0]);
    expect(index.get('pryvit')).toBe(SAMPLE_ROWS[0]);
    expect(index.get('ПРИВІТ'.toLocaleLowerCase())).toBe(SAMPLE_ROWS[0]);
  });

  test('skips rows missing a lemma or slug key', () => {
    const index = buildAtlasAttestationIndex([{ l: '', s: '', g: null }]);
    expect(index.size).toBe(0);
  });
});

describe('classifyPasteCandidates', () => {
  const index = buildAtlasAttestationIndex(SAMPLE_ROWS);

  test('marks an Atlas-attested word with real CEFR + gloss, selected by default', () => {
    const [candidate] = classifyPasteCandidates(['привіт'], index);
    expect(candidate).toMatchObject({
      text: 'привіт',
      status: 'atlas_attested',
      cefr: 'A1',
      atlasSlug: 'pryvit',
      gloss: 'hello',
      selected: true,
    });
  });

  test('matches case-insensitively', () => {
    const [candidate] = classifyPasteCandidates(['ПРИВІТ'], index);
    expect(candidate.status).toBe('atlas_attested');
  });

  test('flags a word absent from the Atlas index as unverified, deselected, with no invented data', () => {
    const [candidate] = classifyPasteCandidates(['вигаданеслово'], index);
    expect(candidate).toEqual({
      text: 'вигаданеслово',
      cefr: null,
      status: 'unverified',
      atlasSlug: null,
      gloss: null,
      selected: false,
    });
  });

  test('keeps a glossed Atlas row with no CEFR selected without inventing a level', () => {
    const [candidate] = classifyPasteCandidates(['ґудзик'], index);
    expect(candidate).toMatchObject({
      status: 'atlas_attested',
      cefr: null,
      gloss: 'button',
      selected: true,
    });
  });

  test('keeps an attested row with no CEFR and no gloss deselected', () => {
    const [candidate] = classifyPasteCandidates(['абракадабра'], index);
    expect(candidate).toMatchObject({
      status: 'atlas_attested',
      cefr: null,
      gloss: null,
      selected: false,
    });
  });

  test('treats a blank Atlas gloss as null rather than an empty invented string', () => {
    const rows: AtlasAttestationRow[] = [{ l: 'тест', s: 'test', g: '   ', c: 'B1' }];
    const [candidate] = classifyPasteCandidates(['тест'], buildAtlasAttestationIndex(rows));
    expect(candidate.gloss).toBeNull();
  });
});

describe('summarizePasteCandidates', () => {
  test('tallies selection, attestation, and per-level counts', () => {
    const index = buildAtlasAttestationIndex(SAMPLE_ROWS);
    const candidates = classifyPasteCandidates(
      ['привіт', 'книжка', 'вигаданеслово'],
      index,
    );
    const summary = summarizePasteCandidates(candidates);
    expect(summary.total).toBe(3);
    expect(summary.attested).toBe(2);
    expect(summary.unverified).toBe(1);
    // unverified candidates default to deselected, so only the two attested count
    expect(summary.selected).toBe(2);
    expect(summary.byLevel.A1).toBe(1);
    expect(summary.byLevel.A2).toBe(1);
    expect(summary.byLevel.B1).toBe(0);
  });

  test('counts a glossed attested word with no CEFR as selected but not leveled', () => {
    const index = buildAtlasAttestationIndex(SAMPLE_ROWS);
    const candidates = classifyPasteCandidates(
      ['привіт', 'ґудзик', 'абракадабра'],
      index,
    );
    const summary = summarizePasteCandidates(candidates);
    expect(summary.total).toBe(3);
    // all three resolve to real Atlas rows, so all count as attested...
    expect(summary.attested).toBe(3);
    // ...the glossed no-CEFR row remains selected but is not invented as A1
    expect(summary.selected).toBe(2);
    expect(summary.byLevel.A1).toBe(1);
  });

  test('excludes deselected candidates from the level tally even if attested', () => {
    const index = buildAtlasAttestationIndex(SAMPLE_ROWS);
    const candidates = classifyPasteCandidates(['привіт'], index).map((c) => ({
      ...c,
      selected: false,
    }));
    const summary = summarizePasteCandidates(candidates);
    expect(summary.selected).toBe(0);
    expect(summary.byLevel.A1).toBe(0);
  });
});

describe('isSaveEligiblePasteCandidate (#6073 F001 — fail-closed save gate)', () => {
  const index = buildAtlasAttestationIndex(SAMPLE_ROWS);

  test('an atlas-attested word with a real CEFR level is save-eligible', () => {
    const [candidate] = classifyPasteCandidates(['привіт'], index);
    expect(isSaveEligiblePasteCandidate(candidate)).toBe(true);
  });

  test('an atlas-attested word with a real gloss but no CEFR is save-eligible', () => {
    const [candidate] = classifyPasteCandidates(['ґудзик'], index);
    expect(isSaveEligiblePasteCandidate(candidate)).toBe(true);
  });

  test('an unverified word is never save-eligible, even if manually selected', () => {
    const [candidate] = classifyPasteCandidates(['вигаданеслово'], index);
    expect(isSaveEligiblePasteCandidate({ ...candidate, selected: true })).toBe(false);
  });

  test('an attested word without a gloss is never save-eligible, even if manually selected', () => {
    const [candidate] = classifyPasteCandidates(['абракадабра'], index);
    expect(isSaveEligiblePasteCandidate({ ...candidate, selected: true })).toBe(false);
  });
});

describe('selectSaveEligiblePasteCandidates (#6073 F001 — final materialization gate)', () => {
  const index = buildAtlasAttestationIndex(SAMPLE_ROWS);

  test('keeps only selected candidates that are also save-eligible', () => {
    const candidates: PasteCandidate[] = classifyPasteCandidates(
      ['привіт', 'книжка', 'ґудзик', 'вигаданеслово', 'абракадабра'],
      index,
    );
    // Simulate a bulk-select/individual-click bug upstream that force-selected
    // ineligible rows anyway — the materialization gate must still reject them.
    const corrupted = candidates.map((c) => ({ ...c, selected: true }));
    const materialized = selectSaveEligiblePasteCandidates(corrupted);

    expect(materialized.map((c) => c.text)).toEqual(['привіт', 'книжка', 'ґудзик']);
  });

  test('drops a save-eligible candidate the user deselected', () => {
    const candidates = classifyPasteCandidates(['привіт'], index).map((c) => ({
      ...c,
      selected: false,
    }));
    expect(selectSaveEligiblePasteCandidates(candidates)).toEqual([]);
  });
});

describe('extraction feeds classification end-to-end', () => {
  test('paste-text tokenization output classifies cleanly against an Atlas index', () => {
    const { lemmaKeys } = parsePlainTextWithTranslations('Привіт! Це моя книжка.');
    const index = buildAtlasAttestationIndex(SAMPLE_ROWS);
    const candidates = classifyPasteCandidates(lemmaKeys, index);
    const byText = new Map(candidates.map((c) => [c.text, c]));
    expect(byText.get('привіт')?.status).toBe('atlas_attested');
    expect(byText.get('книжка')?.status).toBe('atlas_attested');
    // "це" and "моя" are not in the sample index, so must be flagged, never invented.
    expect(byText.get('це')?.status).toBe('unverified');
    expect(byText.get('моя')?.status).toBe('unverified');
  });
});
