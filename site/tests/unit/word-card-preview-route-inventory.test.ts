import { describe, expect, it } from 'vitest';
import { resolve } from 'node:path';
import { statSync } from 'node:fs';
import { publicReleasePin, releasePreviewInputs } from '../../src/lib/lexicon/word-card-preview-inputs';
import { pagePath } from '../../src/lib/lexicon/word-card-readable';
import { ROUTE_CLASSES, ROUTE_INVENTORY_SCHEMA, routeDifferences, routeInventory, type RouteInventory } from '../../src/lib/lexicon/word-card-preview-route-inventory';
import committed from '../../src/lib/lexicon/word-card-preview-route-inventory.json';
import { pins } from '../fixtures/word-card-preview/release-controls';

const inventory = committed as RouteInventory;
const controlled = { enabled: true, controlled: true, artifactPath: resolve('tests/fixtures/word-card-preview/release-jsonl'), pin: JSON.stringify(pins.jsonl) };
const bytes = { dataset_bytes: 1, manifest_bytes: 2 };

describe('route inventory producer', () => {
  it('lists every emitted route of a controlled release once, with each card disposition', () => {
    const result = routeInventory(releasePreviewInputs(controlled), bytes);
    expect(result.routes).toEqual([
      ['compare/release/', 'compare-release-summary'], ['compare/release/wc_0123456789ab/', 'compare-card-diagnostic'],
      ['compare/release/wc_0123456789ac/', 'compare-card-diagnostic'], ['compare/word/fixture-head/', 'compare-word-page'],
      ['release/', 'release-summary'], ['release/wc_0123456789ab/', 'card-diagnostic'], ['release/wc_0123456789ac/', 'card-diagnostic'],
      ['word/fixture-head/', 'word-page'],
    ].map(([path, name]) => ({ path: `/lexicon-v2/${path}`, href: `/lexicon-v2/${path}`, class: name })));
    expect(result.cards.map(c => [c.card_id, c.page, c.entry, c.listed])).toEqual([['wc_0123456789ab', 'fixture-head', 1, true], ['wc_0123456789ac', 'fixture-head', 2, true]]);
    expect(result.counts).toMatchObject({ source_cards: 2, page_keys: 1, learner_pages: 1, visible_entries: 2, proper_only_unlisted: 0, emitted_routes: 8 });
    expect(result.release).toEqual({ ...pins.jsonl, ...bytes });
  });
  it('has no inventory for a refused release', () => {
    expect(() => routeInventory(releasePreviewInputs({ ...controlled, controlled: false }), bytes)).toThrow('No pinned release');
  });
  it('refuses an unknown input kind and a duplicated route', () => {
    const inputs = releasePreviewInputs(controlled);
    expect(() => routeInventory([...inputs, { ...inputs[1]!, card: { kind: 'unavailable', keys: null, claimantId: null, reason: 'x' } }], bytes)).toThrow('Unexpected preview input');
    expect(() => routeInventory([...inputs, inputs[1]!], bytes)).toThrow('Duplicate preview routes: /lexicon-v2/compare/release/wc_0123456789ab/, /lexicon-v2/release/wc_0123456789ab/');
  });
  it('reports omitted, unexpected and duplicated routes', () => {
    expect(routeDifferences(['/a/', '/b/'], ['/b/', '/a/'])).toEqual({ missing: [], unexpected: [], duplicated: [] });
    expect(routeDifferences(['/a/', '/b/', '/b/'], ['/a/', '/c/', '/c/'])).toEqual({ missing: ['/b/'], unexpected: ['/c/'], duplicated: ['/b/', '/c/'] });
  });
});

describe('committed public route inventory', () => {
  const paths = inventory.routes.map(r => r.path);
  const pages = [...new Set(inventory.cards.filter(c => c.listed).map(c => c.page))];
  it('binds the frozen public release pin', () => {
    expect(inventory.schema_version).toBe(ROUTE_INVENTORY_SCHEMA);
    expect(inventory.release).toEqual({ ...publicReleasePin, dataset_bytes: 2879813, manifest_bytes: 3292 });
  });
  it('lists each route once, in path order, with consistent counts', () => {
    expect(routeDifferences(paths, [...paths].sort()).duplicated).toEqual([]);
    expect(paths).toEqual([...paths].sort((a, b) => a < b ? -1 : a > b ? 1 : 0));
    expect(inventory.counts.emitted_routes).toBe(paths.length);
    expect(Object.keys(inventory.counts.routes_by_class)).toEqual(ROUTE_CLASSES);
    for (const name of ROUTE_CLASSES) expect(inventory.counts.routes_by_class[name], name).toBe(inventory.routes.filter(r => r.class === name).length);
  });
  it('derives every route from a source card or a learner page and nothing else', () => {
    const expected = ['', 'compare/'].flatMap(prefix => [`/lexicon-v2/${prefix}release/`,
      ...inventory.cards.map(c => `/lexicon-v2/${prefix}release/${c.card_id}/`), ...pages.map(page => `/lexicon-v2/${prefix}word/${page}/`)]);
    expect(routeDifferences(expected, paths)).toEqual({ missing: [], unexpected: [], duplicated: [] });
    for (const route of inventory.routes.filter(r => r.class.endsWith('word-page'))) {
      const [, compare, key] = /^\/lexicon-v2\/(compare\/)?word\/(.+)\/$/.exec(route.path) ?? [];
      expect(route.href).toBe(pagePath(key!, Boolean(compare)));
    }
  });
  it('separates the source-card, learner-page, entry and route denominators', () => {
    const listed = inventory.cards.filter(c => c.listed);
    expect(new Set(inventory.cards.map(c => c.card_id)).size).toBe(inventory.cards.length);
    expect([inventory.cards.length, pages.length, listed.length, inventory.cards.filter(c => !c.listed).map(c => [c.card_id, c.card_kind, c.page])]).toEqual([
      150, 134, 148, [['wc_bz5ypsm3wyj7', 'proper_name', 'шуба'], ['wc_sye0ppkx0dwh', 'proper_name', 'юнеско']]]);
    expect(inventory.counts).toMatchObject({ source_cards: 150, citations: 2978, page_keys: 136, learner_pages: 134, visible_entries: 148,
      proper_entries_listed: listed.filter(c => c.card_kind === 'proper_name').length, proper_only_unlisted: 2, refused_without_key: 0 });
    expect(inventory.counts.emitted_routes).toBe(2 * (1 + inventory.counts.source_cards + inventory.counts.learner_pages));
  });
});

// Actual-release proof is an explicit local configuration; CI controls remain offline.
describe.runIf(process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH)('actual release v0.1.0-pilot', () => {
  it('reproduces the committed inventory exactly from the pinned bytes', () => {
    const artifactPath = process.env.ATLAS_WORD_CARD_PUBLIC_PROOF_PATH!;
    expect(routeInventory(releasePreviewInputs({ enabled: true, controlled: false, artifactPath }), {
      dataset_bytes: statSync(resolve(artifactPath, 'word-cards.jsonl')).size, manifest_bytes: statSync(resolve(artifactPath, 'manifest.json')).size,
    })).toEqual(inventory);
  });
});
