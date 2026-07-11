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
  buildComponentLinkTargets,
  type AtlasPayloadCache,
  type LexiconEntry,
} from '@site/src/lib/lexicon/atlasDb';

type AstroComponent = Parameters<AstroContainer['renderToString']>[0];
interface AstroComponentModule {
  default: AstroComponent;
}

const atlasDbPath = resolve(
  process.env.ATLAS_DB_PATH ?? resolve(process.cwd(), '../data/atlas.db'),
);

// Fixtures live in the real atlas.db:
//  - брати-взяти is a multiword_term whose migrated payload STILL carries a verb
//    paradigm — proving the morphology suppression is load-bearing, not a no-op.
//  - вода is a plain lemma with a noun paradigm — proving lemma pages are unchanged.
const MULTIWORD_FIXTURE = 'брати-взяти';
const LEMMA_FIXTURE = 'вода';

const COMPONENT_LINK_TARGETS = new Map([
  ['домі', 'dim'],
  ['бити', 'byty'],
  ['праці', 'pratsia'],
  ['називний', 'nazyvnyi'],
  ['відмінок', 'vidminok'],
]);

const COMPONENT_LEMMAS: LexiconEntry[] = [
  ['дім', 'dim'],
  ['бити', 'byty'],
  ['праця', 'pratsia'],
  ['називний', 'nazyvnyi'],
  ['відмінок', 'vidminok'],
].map(([lemma, url_slug]) => ({
  lemma,
  url_slug,
  gloss: null,
  entry_type: 'lemma',
  pos: null,
  ipa: null,
  primary_source: 'fixture',
  course_usage: [],
}));

function makeExpressionLikeFixture(entry_type: string, lemma: string): LexiconEntry {
  return {
    lemma,
    url_slug: `fixture-${entry_type}`,
    gloss: 'fixture gloss',
    entry_type,
    pos: 'phrase',
    ipa: null,
    primary_source: 'fixture',
    course_usage: [
      { track: 'a1', module_num: 1, slug: 'fixture-usage', context: 'built_vocabulary' },
    ],
    enrichment: {
      meaning: { definitions: ['fixture meaning'], source: 'fixture-meaning' },
      sources: ['fixture-citation'],
      // Deliberately present: expression-like templates must suppress it.
      morphology: { pos: 'noun', form_count: 1, forms: [], source: 'fixture-morphology' },
    },
  };
}

function makeHomonymFixture(withHomonyms: boolean): LexiconEntry {
  return {
    ...makeExpressionLikeFixture('lemma', 'коса'),
    sections: withHomonyms
      ? {
          homonyms: {
            items: [
              {
                word: 'коса',
                homonym_no: 2,
                pos: 'ж.',
                gloss: 'сільськогосподарське знаряддя для косіння трави',
              },
            ],
            source: 'СУМ-20',
            source_urls: ['https://slovnyk.me/dict/newsum/коса'],
          },
        }
      : undefined,
  };
}

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

  function renderFixture(
    entry: LexiconEntry,
    componentLinkTargets = COMPONENT_LINK_TARGETS,
  ): Promise<string> {
    return container.renderToString(WordAtlasArticle, {
      props: {
        entry,
        allEntries: COMPONENT_LEMMAS,
        componentLinkTargets,
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

  test.each([
    ['expression', 'у до́мі', 'вираз', 'до́мі', 'dim', 'у'],
    ['phraseologism', 'бити байдики', 'фразеологізм', 'бити', 'byty', 'байдики'],
    ['proverb', 'без праці нема калача', "прислів'я", 'праці', 'pratsia', 'без'],
    ['multiword_term', 'називний відмінок', 'термін', 'називний', 'nazyvnyi', null],
  ])(
    'renders %s as a detail page with safe component backlinks',
    async (entryType, lemma, entryTypeLabel, linkedComponent, linkedSlug, unresolvedComponent) => {
      const html = await renderFixture(makeExpressionLikeFixture(entryType, lemma));

      expect(html.replace(/&#39;/g, "'")).toContain(`Лексикон · ${entryTypeLabel}`);
      expect(html).toContain(`data-expression-detail="${entryType}"`);
      expect(html).toContain('Складники:');
      expect(html).toContain('fixture meaning');
      expect(html).toContain('fixture-citation');
      expect(html).toContain('fixture-usage');
      expect(html).toContain(`href="/lexicon/${linkedSlug}/"`);
      expect(html).toMatch(
        new RegExp(`>${linkedComponent.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}</a>`),
      );
      if (unresolvedComponent) {
        expect(html).toContain(`<span class="chip">${unresolvedComponent}</span>`);
      }
      expect(html).not.toContain('paradigm-table');
      expect(html).not.toContain('Морфологія');
    },
  );

  test('component_cross_links resolves a stress-marked alias and never emits a broken target', async () => {
    const html = await renderFixture(makeExpressionLikeFixture('expression', 'у до́мі'));

    expect(html).toContain('href="/lexicon/dim/"');
    expect(html).not.toContain('href="/lexicon/у/"');
    expect(html).not.toContain('href="/lexicon/до́мі/"');
  });

  test('renders a numbered homonym with its gloss and source', async () => {
    const html = await renderFixture(makeHomonymFixture(true));

    expect(html).toContain('Омонім');
    expect(html).toContain('<h2>Омоніми</h2>');
    expect(html).toContain('коса<sup>2</sup>');
    expect(html).toContain('сільськогосподарське знаряддя для косіння трави');
    expect(html).toContain('Джерела омонімів:');
    expect(html).toContain('href="https://slovnyk.me/dict/newsum/коса"');
    expect(html).toContain('<span class="src">СУМ-20</span>');
  });

  test('keeps the homonym section absent when the entry has no homonym data', async () => {
    const html = await renderFixture(makeHomonymFixture(false));

    expect(html).toContain('Омонім');
    expect(html).not.toContain('<h2>Омоніми</h2>');
    expect(html).not.toContain('Джерела омонімів:');
  });

  test('lemma baseline remains byte-identical before and after entry-type branching', async () => {
    const entry = makeExpressionLikeFixture('lemma', 'дім');
    const { entry_type: _entryType, ...preEntryModelEntry } = entry;

    const before = await renderFixture(preEntryModelEntry);
    const after = await renderFixture(entry);

    expect(after).toBe(before);
  });
});

describe('component-link target resolution (#4385)', () => {
  test('prefers direct approved article heads, uses unique aliases, and suppresses ambiguity', () => {
    const targets = buildComponentLinkTargets(
      [{ lookup_text: 'дім', target_slug: 'dim' }],
      [
        { lookup_text: 'дім', target_slug: 'other-dim' },
        { lookup_text: 'домі', target_slug: 'dim' },
        { lookup_text: 'спірний', target_slug: 'one' },
        { lookup_text: 'спірний', target_slug: 'two' },
      ],
    );

    expect(targets.get('дім')).toBe('dim');
    expect(targets.get('домі')).toBe('dim');
    expect(targets.has('спірний')).toBe(false);
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
