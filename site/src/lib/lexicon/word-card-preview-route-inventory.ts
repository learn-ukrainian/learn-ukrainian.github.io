import { previewStaticPaths, type PreviewInput } from './word-card-preview-inputs';
import { groupReleasePages } from './word-card-readable';
import type { ReleasePin } from './word-card-release';

export const ROUTE_INVENTORY_SCHEMA = 'word-card-preview-route-inventory.v1';
const CLASSES: Record<string, string> = { release: 'release-summary', 'release-card': 'card-diagnostic', 'release-page': 'word-page' };
export const ROUTE_CLASSES = Object.values(CLASSES).flatMap(name => [name, `compare-${name}`]);

export type InventoryRoute = { path: string; href: string; class: string };
export type InventoryCard = { card_id: string; card_kind: string; page: string | null; entry: number | null; listed: boolean; reason: string };
export type RouteInventory = {
  schema_version: string;
  release: ReleasePin & { dataset_bytes: number; manifest_bytes: number };
  counts: {
    source_cards: number; citations: number; page_keys: number; learner_pages: number; visible_entries: number;
    proper_entries_listed: number; proper_only_unlisted: number; refused_without_key: number;
    emitted_routes: number; routes_by_class: Record<string, number>;
  };
  routes: InventoryRoute[];
  cards: InventoryCard[];
};

const byPath = (a: InventoryRoute, b: InventoryRoute) => a.path < b.path ? -1 : a.path > b.path ? 1 : 0;

/**
 * Every route the preview page emits for one pinned release, derived from the same inputs and static-path producer
 * the page uses, with each source card's page disposition. A refused release has no inventory.
 */
export function routeInventory(inputs: PreviewInput[], bytes: { dataset_bytes: number; manifest_bytes: number }): RouteInventory {
  const summary = inputs.find(input => input.card.kind === 'release')?.card;
  if (summary?.kind !== 'release') throw Error('No pinned release among the preview inputs');
  const { pages, dispositions } = groupReleasePages(summary.rows);
  const routes = previewStaticPaths(inputs).map(({ params, props }) => {
    const base = CLASSES[props.card.kind];
    if (!base) throw Error(`Unexpected preview input ${props.name}`);
    return { path: `/lexicon-v2/${params.path}/`, href: `/lexicon-v2/${params.path.split('/').map(encodeURIComponent).join('/')}/`,
      class: props.compare ? `compare-${base}` : base };
  }).sort(byPath);
  const duplicated = routeDifferences(routes.map(r => r.path), routes.map(r => r.path)).duplicated;
  if (duplicated.length) throw Error(`Duplicate preview routes: ${duplicated.join(', ')}`);
  const entries = pages.flatMap(page => page.entries);
  return {
    schema_version: ROUTE_INVENTORY_SCHEMA,
    release: { ...summary.pin, ...bytes },
    counts: {
      source_cards: summary.rows.length,
      citations: summary.rows.reduce((n, row) => n + row.fields.length, 0),
      page_keys: new Set(dispositions.flatMap(d => d.key === null ? [] : [d.key])).size,
      learner_pages: pages.length,
      visible_entries: entries.length,
      proper_entries_listed: entries.filter(entry => entry.proper).length,
      proper_only_unlisted: dispositions.filter(d => !d.listed && d.key !== null && d.cardKind === 'proper_name').length,
      refused_without_key: dispositions.filter(d => d.key === null).length,
      emitted_routes: routes.length,
      routes_by_class: Object.fromEntries(ROUTE_CLASSES.map(name => [name, routes.filter(r => r.class === name).length])),
    },
    routes,
    cards: dispositions.map(d => ({ card_id: d.cardId, card_kind: d.cardKind, page: d.key, entry: d.ordinal, listed: d.listed, reason: d.reason })),
  };
}

/** Routes omitted from, unexpected in, or repeated in either list. All empty means the sets agree exactly. */
export function routeDifferences(expected: string[], emitted: string[]) {
  const repeated = (paths: string[]) => paths.filter((path, i) => paths.indexOf(path) !== i);
  const want = new Set(expected), got = new Set(emitted);
  return { missing: [...want].filter(path => !got.has(path)), unexpected: [...got].filter(path => !want.has(path)),
    duplicated: [...new Set([...repeated(expected), ...repeated(emitted)])] };
}
