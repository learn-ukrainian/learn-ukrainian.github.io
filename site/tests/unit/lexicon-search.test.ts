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
