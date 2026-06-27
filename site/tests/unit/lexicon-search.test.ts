import { describe, expect, test } from 'vitest';
import { highlight, normalize, rankMatches, type SearchRow } from '@site/src/lib/lexicon/search';

const rows: SearchRow[] = [
  { l: 'заофісний', s: 'zaofisnyi', g: 'back room', r: 'zaofisnyi', k: 'other' },
  { l: 'офіс', s: 'ofis', g: 'workplace', r: 'ofis', k: 'vyv' },
  { l: 'офісний', s: 'ofisnyi', g: 'work-related', r: 'ofisnyi', k: 'vyv' },
  { l: 'офіціант', s: 'ofitsiant', g: 'waiter', r: 'ofitsiant', k: 'vyv' },
  { l: 'пошта', s: 'poshta', g: 'office', r: 'poshta', k: 'other' },
];

describe('lexicon search helpers', () => {
  test('normalizes case, whitespace, and composed Unicode', () => {
    expect(normalize('  ОФІС  ')).toBe('офіс');
    expect(normalize('e\u0301')).toBe('é');
  });

  test('strips Ukrainian stress accents while preserving й, ї, and Latin accents', () => {
    // Cyrillic stress marks (U+0301) are stripped so plain typing matches accented lemmas.
    expect(normalize('на́голос')).toBe('наголос');
    expect(normalize('авантю́рний')).toBe('авантюрний');
    // The breve composing й (и+U+0306) and diaeresis composing ї (і+U+0308) survive NFC + strip.
    expect(normalize('й')).toBe('й');
    expect(normalize('ї')).toBe('ї');
    // Precomposed Latin accents are untouched (regression guard for the NFC behavior).
    expect(normalize('é')).toBe('é');
  });

  test('finds a stress-accented lemma by a plain (unaccented) query', () => {
    const accented: SearchRow[] = [
      { l: 'авантю́рний', s: 'avantiurnyi', g: 'adventurous', r: 'avantiurnyi', k: 'vyv' },
    ];
    expect(rankMatches(accented, 'авантюрний').map((row) => row.l)).toEqual(['авантю́рний']);
  });

  test('matches Cyrillic lemma prefixes', () => {
    expect(rankMatches(rows, 'офі', 3).map((row) => row.l)).toEqual(['офіс', 'офісний', 'офіціант']);
  });

  test('matches Latin romanized prefixes', () => {
    expect(rankMatches(rows, 'ofis').map((row) => row.l)).toEqual(['офіс', 'офісний', 'заофісний']);
  });

  test('matches English glosses for Latin queries', () => {
    expect(rankMatches(rows, 'office').map((row) => row.l)).toEqual(['пошта']);
  });

  test('orders exact, prefix, romanized, substring, and gloss tiers deterministically', () => {
    expect(rankMatches(rows, 'офіс').map((row) => row.l)).toEqual([
      'офіс',
      'офісний',
      'заофісний',
    ]);
  });

  test('escapes highlighted HTML safely', () => {
    expect(highlight('<b>офіс</b>', 'офіс')).toBe('&lt;b&gt;<mark>офіс</mark>&lt;/b&gt;');
  });

  test('returns no matches for an empty query', () => {
    expect(rankMatches(rows, '   ')).toEqual([]);
  });
});
