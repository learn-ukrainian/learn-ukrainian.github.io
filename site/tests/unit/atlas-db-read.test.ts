// @vitest-environment node

import Database from 'better-sqlite3';
import { describe, expect, test, vi, afterEach, beforeEach } from 'vitest';
import { resolve } from 'node:path';
import * as fs from 'node:fs';
import {
  getAtlasPayloadCache,
  resetAtlasPayloadCacheForTests,
  getPracticeLemmas,
  type LexiconEntry,
} from '@site/src/lib/lexicon/atlasDb';
import { articleProps } from '../helpers/word-atlas-record';
import { renderWordAtlasArticle } from '../helpers/render-word-atlas-article';

// Static JSON import fails napi string conversion on large hydrated manifests
// (~15k+ entries after textbook promote). Load with fs + JSON.parse instead.
const manifest = JSON.parse(
  fs.readFileSync(resolve(process.cwd(), 'src/data/lexicon-manifest.json'), 'utf8'),
) as {
  version: string;
  generated_at: string;
  entries: LexiconEntry[];
};

let mockExistsSync = (p: string): boolean => true;
let mockReadFileSync = (p: string, encoding: any): string => '';

vi.mock('node:fs', async (importOriginal) => {
  const actual = await importOriginal<typeof import('node:fs')>();
  return {
    ...actual,
    existsSync: (p: any) => {
      if (typeof p === 'string' && p.includes('practice-index')) {
        return mockExistsSync(p);
      }
      return actual.existsSync(p);
    },
    readFileSync: (p: any, options: any) => {
      if (typeof p === 'string' && p.includes('practice-index')) {
        return mockReadFileSync(p, options);
      }
      return actual.readFileSync(p, options);
    },
  };
});

interface LexiconManifest {
  version: string;
  generated_at: string;
  entries: LexiconEntry[];
}

interface EntryTypeRow {
  entry_type: string;
  slug: string;
}

const data = manifest as LexiconManifest;
const atlasDbPath = resolve(process.cwd(), '../data/atlas.db');
const requiredFixtureSlugs = [
  'прапор',
  'файний',
  'будь-ласка',
  'доконаний-вид',
  'ілля',
  'іване',
];

function isCurrentRouteEntry(entry: LexiconEntry): boolean {
  return Boolean(entry.lemma) && Boolean(entry.url_slug) && entry.pos !== 'grammar term';
}

function manifestRouteEntries(): LexiconEntry[] {
  return data.entries.filter(isCurrentRouteEntry);
}

function readEntryTypeFixtures(): EntryTypeRow[] {
  const db = new Database(atlasDbPath, { readonly: true, fileMustExist: true });
  try {
    return db
      .prepare(
        `SELECT entry_type, MIN(slug) AS slug
         FROM articles
         WHERE review_state = 'approved'
           AND visibility = 'public'
         GROUP BY entry_type
         ORDER BY entry_type`,
      )
      .all() as EntryTypeRow[];
  } finally {
    db.close();
  }
}

function firstDifference(left: string, right: string): string {
  const limit = Math.min(left.length, right.length);
  for (let index = 0; index < limit; index += 1) {
    if (left[index] !== right[index]) {
      return `first difference at ${index}: manifest=${JSON.stringify(left.slice(index, index + 120))} db=${JSON.stringify(right.slice(index, index + 120))}`;
    }
  }
  return `length differs: manifest=${left.length} db=${right.length}`;
}

describe('Atlas DB SSG read parity', () => {
  test('preloaded DB payloads preserve the current manifest route surface', async () => {
    resetAtlasPayloadCacheForTests();
    const cache = getAtlasPayloadCache();
    const manifestEntries = manifestRouteEntries();

    expect(cache.entries.map((entry) => entry.url_slug)).toEqual(
      manifestEntries.map((entry) => entry.url_slug),
    );
    expect(cache.generatedAt).toBe(data.generated_at);
    expect(cache.manifestVersion).toBe(data.version);

    const paths = cache.entries.map((entry) => ({
      params: { lemma: entry.url_slug },
      props: { entry },
    }));
    expect(paths.map((path) => path.params.lemma)).toEqual(cache.entries.map((entry) => entry.url_slug));
  });

  test('renders DB payload HTML byte-identical to manifest payload HTML for parity fixtures', async () => {
    resetAtlasPayloadCacheForTests();
    const cache = getAtlasPayloadCache();
    const manifestEntries = manifestRouteEntries();
    const manifestBySlug = new Map(manifestEntries.map((entry) => [entry.url_slug, entry]));
    const fixtureSlugs = Array.from(
      new Set([...requiredFixtureSlugs, ...readEntryTypeFixtures().map((row) => row.slug)]),
    );
    let differing = 0;

    for (const slug of fixtureSlugs) {
      const manifestEntry = manifestBySlug.get(slug);
      const dbEntry = cache.bySlug.get(slug);
      expect(manifestEntry, `manifest fixture missing: ${slug}`).toBeDefined();
      expect(dbEntry, `DB fixture missing: ${slug}`).toBeDefined();
      // entry_type is a DB-only field (the manifest predates the entry model).
      // Align the manifest fixture with the DB's entry_type so this parity check
      // isolates payload-projection fidelity from entry_type branching, which is
      // covered by atlas-entry-type-templates.test.ts.
      const alignedManifestEntry = { ...manifestEntry!, entry_type: dbEntry!.entry_type };
      expect(dbEntry).toEqual(alignedManifestEntry);

      const manifestHtml = renderWordAtlasArticle(articleProps(alignedManifestEntry, {
        lemmaEntries: manifestEntries,
        generatedAt: data.generated_at,
        manifestVersion: data.version,
      }));
      const dbHtml = renderWordAtlasArticle(articleProps(dbEntry!, {
        lemmaEntries: cache.entries,
        generatedAt: cache.generatedAt,
        manifestVersion: cache.manifestVersion,
      }));

      if (manifestHtml !== dbHtml) {
        differing += 1;
        throw new Error(`golden diff not empty for ${slug}: ${firstDifference(manifestHtml, dbHtml)}`);
      }
    }

    process.stdout.write(`atlas render parity golden diff: fixtures=${fixtureSlugs.length} differing=${differing}\n`);
    expect(differing).toBe(0);
  });
});

describe('getPracticeLemmas', () => {
  beforeEach(() => {
    resetAtlasPayloadCacheForTests();
    mockExistsSync = () => true;
    mockReadFileSync = () => '';
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  test('returns the expected lemma set from a fixture practice-index file', () => {
    mockExistsSync = (p) => String(p).includes('practice-index.A1.json');
    mockReadFileSync = (p) => {
      if (String(p).includes('practice-index.A1.json')) {
        return JSON.stringify({
          items: [
            { lemmaId: 'prapor' },
            { lemmaId: 'fainyi' },
            { lemmaId: '' },
          ],
        });
      }
      throw new Error('Not found');
    };

    const lemmas = getPracticeLemmas();
    expect(lemmas).toBeInstanceOf(Set);
    expect(lemmas.has('prapor')).toBe(true);
    expect(lemmas.has('fainyi')).toBe(true);
    expect(lemmas.size).toBe(2);
  });

  test('returns empty set and warns when no path resolves', () => {
    mockExistsSync = () => false;
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const lemmas = getPracticeLemmas();
    expect(lemmas.size).toBe(0);
    expect(warnSpy).toHaveBeenCalledTimes(1);
    expect(warnSpy.mock.calls[0][0]).toContain('failed to resolve any practice-index files');
  });
});
