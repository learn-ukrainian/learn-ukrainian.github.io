// @vitest-environment node

import Database from 'better-sqlite3';
import reactRenderer from '@astrojs/react/server.js';
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { describe, expect, test, beforeAll, vi } from 'vitest';
import { resolve } from 'node:path';
import {
  getAtlasPayloadCache,
  resetAtlasPayloadCacheForTests,
  runEntryModelGates,
  type AtlasPayloadCache,
  type LexiconEntry,
} from '@site/src/lib/lexicon/atlasDb';

type AstroComponent = Parameters<AstroContainer['renderToString']>[0];
interface AstroComponentModule {
  default: AstroComponent;
}

const atlasDbPath = resolve(process.cwd(), '../data/atlas.db');

// Fixtures live in the real atlas.db:
//  - брати-взяти is a multiword_term whose migrated payload STILL carries a verb
//    paradigm — proving the morphology suppression is load-bearing, not a no-op.
//  - вода is a plain lemma with a noun paradigm — proving lemma pages are unchanged.
const MULTIWORD_FIXTURE = 'брати-взяти';
const LEMMA_FIXTURE = 'вода';

/** Minimal in-memory atlas.db shaped like the entry-model schema for gate tests. */
function makeFixtureDb(): InstanceType<typeof Database> {
  const db = new Database(':memory:');
  db.exec(`
    CREATE TABLE articles (
      slug TEXT PRIMARY KEY, display_head TEXT, lemma TEXT, entry_type TEXT,
      review_state TEXT, visibility TEXT
    );
    CREATE TABLE article_payloads (
      slug TEXT PRIMARY KEY, route_order INTEGER, payload_json TEXT, is_public_route INTEGER
    );
    CREATE TABLE aliases (
      alias TEXT, kind TEXT, source TEXT, target_slug TEXT, visibility TEXT DEFAULT 'public'
    );
  `);
  return db;
}

describe('entry_type-branched article rendering (#4385)', () => {
  let container: AstroContainer;
  let WordAtlasArticle: AstroComponent;
  let cache: AtlasPayloadCache;

  beforeAll(async () => {
    resetAtlasPayloadCacheForTests();
    cache = getAtlasPayloadCache();
    ({ default: WordAtlasArticle } = (await import(
      '@site/src/lexicon/WordAtlasArticle.astro'
    )) as AstroComponentModule);
    container = await AstroContainer.create();
    container.addServerRenderer({ renderer: reactRenderer });
  });

  async function render(entry: LexiconEntry | undefined, slug: string): Promise<string> {
    expect(entry, `fixture missing: ${slug}`).toBeDefined();
    return container.renderToString(WordAtlasArticle, {
      props: {
        entry,
        allEntries: cache.entries,
        generatedAt: 'test',
        manifestVersion: 'test',
      },
    });
  }

  test('entry_type is joined onto payloads from the articles table', () => {
    expect(cache.bySlug.get(MULTIWORD_FIXTURE)?.entry_type).toBe('multiword_term');
    expect(cache.bySlug.get(LEMMA_FIXTURE)?.entry_type).toBe('lemma');
    // form_of alias routes have no articles row → entry_type is null, not undefined.
    const formOf = cache.entries.find((entry) => entry.form_of);
    expect(formOf, 'expected at least one form_of alias route in the fixture DB').toBeDefined();
    expect(formOf?.entry_type).toBeNull();

    // The multiword payload genuinely carries a paradigm, so suppression matters.
    const morphology = (
      cache.bySlug.get(MULTIWORD_FIXTURE)?.enrichment as
        | { morphology?: { paradigm?: { kind?: string } } }
        | null
        | undefined
    )?.morphology;
    expect(morphology?.paradigm?.kind).toBe('verb');
  });

  test('multiword_term renders via the non-lemma template — no paradigm/morphology', async () => {
    const html = await render(cache.bySlug.get(MULTIWORD_FIXTURE), MULTIWORD_FIXTURE);
    // No case/paradigm table and no morphology section or overview card at all.
    expect(html).not.toContain('paradigm-table');
    expect(html).not.toContain('Морфологія');
    // The non-lemma template still renders the headword.
    expect(html).toContain('word-title');
  });

  test('lemma renders unchanged — paradigm/morphology section present', async () => {
    const html = await render(cache.bySlug.get(LEMMA_FIXTURE), LEMMA_FIXTURE);
    expect(html).toContain('paradigm-table');
    expect(html).toContain('Морфологія');
  });
});

describe('runEntryModelGates — site-build assertions (#4385)', () => {
  test('passes on a valid entry-model DB and returns the aggregate counts', () => {
    const db = makeFixtureDb();
    db.prepare(`INSERT INTO articles VALUES ('good', 'g', 'g', 'lemma', 'approved', 'public')`).run();
    db.prepare(`INSERT INTO article_payloads VALUES ('good', 0, '{}', 1)`).run();
    db.prepare(`INSERT INTO aliases VALUES ('доброго', 'inflected_form', 'vesum', 'good', 'public')`).run();
    try {
      expect(runEntryModelGates(db)).toEqual({
        reviewedEntries: 1,
        publicRoutes: 1,
        formOfRoutes: 0,
        aliasRecords: 1,
      });
    } finally {
      db.close();
    }
  });

  test('alias_target_integrity: fails loudly on an alias whose target is not an approved public article', () => {
    const db = makeFixtureDb();
    db.prepare(`INSERT INTO articles VALUES ('good', 'g', 'g', 'lemma', 'approved', 'public')`).run();
    db.prepare(`INSERT INTO article_payloads VALUES ('good', 0, '{}', 1)`).run();
    db.prepare(`INSERT INTO aliases VALUES ('привид', 'canonical', 'seed', 'missing-slug', 'public')`).run();
    const errSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    try {
      expect(() => runEntryModelGates(db)).toThrow(/alias target\(s\) are not approved public articles/);
      expect(errSpy).toHaveBeenCalled();
      const message = String(errSpy.mock.calls[0]?.[0] ?? '');
      expect(message).toContain('alias_target_integrity failure');
      expect(message).toContain('missing-slug');
      expect(message).toContain('missing target article');
    } finally {
      errSpy.mockRestore();
      db.close();
    }
  });

  test('article_vs_alias_count: fails when a public route is not a reviewed entry', () => {
    const db = makeFixtureDb();
    db.prepare(`INSERT INTO articles VALUES ('good', 'g', 'g', 'lemma', 'approved', 'public')`).run();
    // A needs_review article that has (wrongly) been given a public route.
    db.prepare(`INSERT INTO articles VALUES ('draft', 'd', 'd', 'lemma', 'needs_review', 'public')`).run();
    db.prepare(`INSERT INTO article_payloads VALUES ('good', 0, '{}', 1)`).run();
    db.prepare(`INSERT INTO article_payloads VALUES ('draft', 1, '{}', 1)`).run();
    try {
      expect(() => runEntryModelGates(db)).toThrow(/article_vs_alias_count failure/);
    } finally {
      db.close();
    }
  });

  test('the production atlas.db satisfies both entry-model gates', () => {
    const db = new Database(atlasDbPath, { readonly: true, fileMustExist: true });
    try {
      const counts = runEntryModelGates(db);
      expect(counts.reviewedEntries).toBeGreaterThan(0);
      expect(counts.reviewedEntries).toBe(counts.publicRoutes - counts.formOfRoutes);
    } finally {
      db.close();
    }
  });
});
