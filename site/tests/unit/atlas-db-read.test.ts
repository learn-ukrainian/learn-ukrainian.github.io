// @vitest-environment node

import Database from 'better-sqlite3';
import reactRenderer from '@astrojs/react/server.js';
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { describe, expect, test } from 'vitest';
import { resolve } from 'node:path';
import manifest from '@site/src/data/lexicon-manifest.json';
import {
  getAtlasPayloadCache,
  resetAtlasPayloadCacheForTests,
  type LexiconEntry,
} from '@site/src/lib/lexicon/atlasDb';

interface LexiconManifest {
  version: string;
  generated_at: string;
  entries: LexiconEntry[];
}

interface EntryTypeRow {
  entry_type: string;
  slug: string;
}

type AstroComponent = Parameters<AstroContainer['renderToString']>[0];

interface AstroComponentModule {
  default: AstroComponent;
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
    const { default: WordAtlasArticle } = (await import(
      '@site/src/lexicon/WordAtlasArticle.astro'
    )) as AstroComponentModule;
    const container = await AstroContainer.create();
    container.addServerRenderer({ renderer: reactRenderer });
    let differing = 0;

    for (const slug of fixtureSlugs) {
      const manifestEntry = manifestBySlug.get(slug);
      const dbEntry = cache.bySlug.get(slug);
      expect(manifestEntry, `manifest fixture missing: ${slug}`).toBeDefined();
      expect(dbEntry, `DB fixture missing: ${slug}`).toBeDefined();
      expect(dbEntry).toEqual(manifestEntry);

      const manifestHtml = await container.renderToString(WordAtlasArticle, {
        props: {
          entry: manifestEntry,
          allEntries: manifestEntries,
          generatedAt: data.generated_at,
          manifestVersion: data.version,
        },
      });
      const dbHtml = await container.renderToString(WordAtlasArticle, {
        props: {
          entry: dbEntry,
          allEntries: cache.entries,
          generatedAt: cache.generatedAt,
          manifestVersion: cache.manifestVersion,
        },
      });

      if (manifestHtml !== dbHtml) {
        differing += 1;
        throw new Error(`golden diff not empty for ${slug}: ${firstDifference(manifestHtml, dbHtml)}`);
      }
    }

    process.stdout.write(`atlas render parity golden diff: fixtures=${fixtureSlugs.length} differing=${differing}\n`);
    expect(differing).toBe(0);
  });
});
