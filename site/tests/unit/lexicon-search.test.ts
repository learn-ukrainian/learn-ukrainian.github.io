import { describe, expect, test } from 'vitest';
import {
  highlight,
  normalize,
  rankMatches,
  rankSearchResults,
  searchShardForQuery,
  searchShardKeysForRow,
  searchShardPrefix,
  type SearchRow,
  type SearchAlias,
  type SearchShardManifest,
} from '@site/src/lib/lexicon/search';

const rows: SearchRow[] = [
  { l: 'заофісний', s: 'zaofisnyi', g: 'back room', r: 'zaofisnyi', k: 'other' },
  { l: 'офіс', s: 'ofis', g: 'workplace', r: 'ofis', k: 'vyv' },
  { l: 'офісний', s: 'ofisnyi', g: 'work-related', r: 'ofisnyi', k: 'vyv' },
  { l: 'офіціант', s: 'ofitsiant', g: 'waiter', r: 'ofitsiant', k: 'vyv' },
  { l: 'пошта', s: 'poshta', g: 'office', r: 'poshta', k: 'other' },
];

const aliases: SearchAlias[] = [
  { a: 'Іване', k: 'inflected_form', s: 'іван', h: 'Іван' },
  { a: 'бачу', k: 'inflected_form', s: 'бачити', h: 'бачити' },
  { a: 'автобусом', k: 'inflected_form', s: 'автобус', h: 'автобус' },
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

  test('resolves aliases to their approved article heads and slugs', () => {
    const articles: SearchRow[] = [
      { l: 'Іван', s: 'іван', g: 'Ivan' },
      { l: 'бачити', s: 'бачити', g: 'to see' },
      { l: 'автобус', s: 'автобус', g: 'bus' },
    ];

    for (const [query, slug, head] of [
      ['Іване', 'іван', 'Іван'],
      ['бачу', 'бачити', 'бачити'],
      ['автобусом', 'автобус', 'автобус'],
    ]) {
      expect(rankSearchResults(articles, aliases, query)).toEqual([
        {
          article: { l: head, s: slug, g: null },
          matchedAlias: query,
          aliasKind: 'inflected_form',
        },
      ]);
    }
  });

  test('prefers a direct article hit and suppresses its duplicate alias resolution', () => {
    const articles: SearchRow[] = [{ l: 'Іван', s: 'іван', g: 'Ivan' }];
    const duplicateAlias: SearchAlias[] = [
      { a: 'Іван', k: 'canonical', s: 'іван', h: 'Іван' },
    ];

    expect(rankSearchResults(articles, duplicateAlias, 'Іван')).toEqual([
      { article: articles[0] },
    ]);
  });

  test('escapes highlighted HTML safely', () => {
    expect(highlight('<b>офіс</b>', 'офіс')).toBe('&lt;b&gt;<mark>офіс</mark>&lt;/b&gt;');
  });

  test('returns no matches for an empty query', () => {
    expect(rankMatches(rows, '   ')).toEqual([]);
  });

  test('selects shard prefixes from normalized query text', () => {
    expect(searchShardPrefix('  ОФІС  ')).toBe('о');
    expect(searchShardPrefix('ofis')).toBe('o');
    expect(searchShardPrefix('авантю́ра')).toBe('а');
    expect(searchShardPrefix('   ')).toBeNull();
  });

  test('resolves query shard metadata through manifest prefix map', () => {
    const manifest: SearchShardManifest = {
      schema: 'atlas-search-shards',
      schemaVersion: 1,
      total: 2,
      fullIndex: { path: '/lexicon/search-index.json', count: 2, bytes: 100, sha256: 'full' },
      shardCount: 2,
      prefixMap: { о: 'u043e', o: 'latin-o' },
      shards: {
        u043e: { path: '/lexicon/search/u043e.json', count: 1, bytes: 10, sha256: 'uk' },
        'latin-o': { path: '/lexicon/search/latin-o.json', count: 1, bytes: 10, sha256: 'latin' },
      },
    };

    expect(searchShardForQuery(manifest, 'офіс')?.path).toBe('/lexicon/search/u043e.json');
    expect(searchShardForQuery(manifest, 'ofis')?.path).toBe('/lexicon/search/latin-o.json');
    expect(searchShardForQuery(manifest, 'x')).toBeNull();
  });

  test('assigns rows to every searchable prefix shard', () => {
    const manifest: SearchShardManifest = {
      schema: 'atlas-search-shards',
      schemaVersion: 1,
      total: 1,
      fullIndex: { path: '/lexicon/search-index.json', count: 1, bytes: 100, sha256: 'full' },
      shardCount: 3,
      prefixMap: { о: 'u043e', o: 'latin-o', w: 'latin-w' },
      shards: {
        u043e: { path: '/lexicon/search/u043e.json', count: 1, bytes: 10, sha256: 'uk' },
        'latin-o': { path: '/lexicon/search/latin-o.json', count: 1, bytes: 10, sha256: 'latin' },
        'latin-w': { path: '/lexicon/search/latin-w.json', count: 1, bytes: 10, sha256: 'gloss' },
      },
    };

    expect(searchShardKeysForRow(manifest, rows[1])).toEqual(['latin-o', 'latin-w', 'u043e']);
  });
});
