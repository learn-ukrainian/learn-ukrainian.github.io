import { normalizeAtlasText } from "./normalize";

export interface SearchRow {
  l: string;
  s: string;
  g: string | null;
  r?: string;
  k?: string;
  c?: string;
  cls?: string;
  t?: string;
}

/** A public-safe query form that resolves to an approved article record. */
export interface SearchAlias {
  a: string;
  k: string;
  s: string;
  h: string;
}

/** A typeahead result always navigates to an article, never to an alias row. */
export interface SearchResult {
  article: SearchRow;
  matchedAlias?: string;
  aliasKind?: string;
}

export interface SearchShardMeta {
  path: string;
  count: number;
  bytes: number;
  sha256: string;
}

export interface SearchShardManifest {
  schema: "atlas-search-shards";
  schemaVersion: 1;
  total: number;
  fullIndex: SearchShardMeta;
  shardCount: number;
  prefixMap: Record<string, string>;
  shards: Record<string, SearchShardMeta>;
}

const CYRILLIC_RE = /[\u0400-\u04ff]/;
const LATIN_RE = /[A-Za-z]/;
const TOKEN_RE = /[\p{L}\p{N}_]+/gu;
const ESCAPE_RE = /[&<>"']/g;
const ESCAPE_MAP: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

function escapeHtml(value: string): string {
  return value.replace(ESCAPE_RE, (c) => ESCAPE_MAP[c] ?? c);
}

function compareByLemma(a: SearchRow, b: SearchRow): number {
  const left = normalizeAtlasText(a.l);
  const right = normalizeAtlasText(b.l);
  if (left < right) return -1;
  if (left > right) return 1;
  return a.s < b.s ? -1 : a.s > b.s ? 1 : 0;
}

function firstTokenChars(value: string | null | undefined): string[] {
  const chars = new Set<string>();
  const normalized = normalize(value ?? "");
  for (const token of normalized.match(TOKEN_RE) ?? []) {
    const first = Array.from(token)[0];
    if (first) chars.add(first);
  }
  return [...chars];
}

export function normalize(q: string): string {
  return normalizeAtlasText(q);
}

export function searchShardPrefix(q: string): string | null {
  const normalized = normalize(q);
  return Array.from(normalized)[0] ?? null;
}

export function searchShardForQuery(
  manifest: SearchShardManifest,
  q: string,
): SearchShardMeta | null {
  const prefix = searchShardPrefix(q);
  if (!prefix) return null;
  const key = manifest.prefixMap[prefix];
  return key ? (manifest.shards[key] ?? null) : null;
}

export function searchShardKeysForRow(
  manifest: SearchShardManifest,
  row: SearchRow,
): string[] {
  const keys = new Set<string>();
  for (const value of [row.l, row.r, row.g]) {
    for (const char of firstTokenChars(value)) {
      const key = manifest.prefixMap[char];
      if (key && manifest.shards[key]) keys.add(key);
    }
  }
  return [...keys].sort();
}

export function buildSearchRowsByShard(
  manifest: SearchShardManifest,
  rows: SearchRow[],
): Map<string, SearchRow[]> {
  const rowsByShard = new Map<string, SearchRow[]>(
    Object.keys(manifest.shards).map((key) => [key, []]),
  );
  for (const row of rows) {
    for (const key of searchShardKeysForRow(manifest, row)) {
      rowsByShard.get(key)?.push(row);
    }
  }
  return rowsByShard;
}

function matchTier(row: SearchRow, nq: string): number | null {
  const hasLatin = LATIN_RE.test(nq);
  const hasCyrillic = CYRILLIC_RE.test(nq);
  const useLemma = hasCyrillic || !hasLatin;
  const useLatin = hasLatin;
  const lemma = normalizeAtlasText(row.l);
  const romanized = row.r ? normalize(row.r) : "";
  const gloss = row.g ? normalize(row.g) : "";

  if (useLemma && lemma === nq) return 0;
  if (useLemma && lemma.startsWith(nq)) return 1;
  if (useLatin && romanized.startsWith(nq)) return 2;
  if (useLemma && lemma.includes(nq)) return 3;
  if (useLatin && romanized.includes(nq)) return 4;
  if (useLatin && gloss.includes(nq)) return 5;
  return null;
}

export function rankMatches(rows: SearchRow[], q: string, limit = 12): SearchRow[] {
  const nq = normalize(q);
  if (!nq || limit <= 0) return [];

  return rows
    .map((row, index) => ({ row, index, tier: matchTier(row, nq) }))
    .filter((item): item is { row: SearchRow; index: number; tier: number } => item.tier !== null)
    .sort((a, b) => a.tier - b.tier || compareByLemma(a.row, b.row) || a.index - b.index)
    .slice(0, limit)
    .map((item) => item.row);
}

function aliasMatchTier(alias: SearchAlias, nq: string): number | null {
  const text = normalize(alias.a);
  if (text === nq) return 0;
  if (text.startsWith(nq)) return 1;
  if (text.includes(nq)) return 3;
  return null;
}

function rankAliasMatches(aliases: SearchAlias[], q: string): SearchAlias[] {
  const nq = normalize(q);
  if (!nq) return [];

  return aliases
    .map((alias, index) => ({ alias, index, tier: aliasMatchTier(alias, nq) }))
    .filter((item): item is { alias: SearchAlias; index: number; tier: number } => item.tier !== null)
    .sort(
      (a, b) =>
        a.tier - b.tier ||
        compareByLemma({ l: a.alias.a, s: a.alias.s, g: null }, { l: b.alias.a, s: b.alias.s, g: null }) ||
        a.index - b.index,
    )
    .map((item) => item.alias);
}

/**
 * Merge independently built article and alias artifacts for typeahead.
 *
 * Article matches always rank first. Alias rows can only add a target slug that
 * is not already represented by a direct article match, so one learner query
 * never renders a dead alias route or a duplicate result for the same article.
 */
export function rankSearchResults(
  articles: SearchRow[],
  aliases: SearchAlias[],
  q: string,
  limit = 12,
): SearchResult[] {
  if (!normalize(q) || limit <= 0) return [];

  const results: SearchResult[] = rankMatches(articles, q, limit).map((article) => ({ article }));
  const seenSlugs = new Set(results.map((result) => result.article.s));
  for (const alias of rankAliasMatches(aliases, q)) {
    if (seenSlugs.has(alias.s)) continue;
    seenSlugs.add(alias.s);
    results.push({
      article: { l: alias.h, s: alias.s, g: null },
      matchedAlias: alias.a,
      aliasKind: alias.k,
    });
    if (results.length >= limit) break;
  }
  return results;
}

export function highlight(text: string, q: string): string {
  const source = String(text).normalize("NFC");
  const needle = normalize(q);
  if (!needle) return escapeHtml(source);

  const haystack = normalizeAtlasText(source);
  const index = haystack.indexOf(needle);
  if (index < 0) return escapeHtml(source);

  const before = source.slice(0, index);
  const match = source.slice(index, index + needle.length);
  const after = source.slice(index + needle.length);
  return `${escapeHtml(before)}<mark>${escapeHtml(match)}</mark>${escapeHtml(after)}`;
}
