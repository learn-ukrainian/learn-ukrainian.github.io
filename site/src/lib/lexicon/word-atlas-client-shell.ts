/**
 * Client word-page shell load/state machine (PR3 D2 + R9).
 *
 * Pure async helpers — hermetic tests stub `AtlasDataSource` / fetch.
 */

import {
  AtlasDataSourceError,
  type AtlasDataSource,
  type EntryRecord,
} from "./atlas-data-source.ts";
import { absoluteSitePath } from "./site-base.ts";
import {
  buildAtlasLinkCatalogFromSearchRows,
  type AtlasLinkCatalog,
  type AtlasSearchAliasRow,
  type AtlasSearchArticleRow,
} from "./word-atlas-article-model.ts";

export type AtlasClientShellState =
  | { status: "loading"; slug: string }
  | {
      status: "ready";
      slug: string;
      record: EntryRecord;
      generatedAt: string;
      manifestVersion: string;
    }
  | { status: "not_found"; slug: string }
  | { status: "corrupt"; slug: string; message: string }
  | { status: "network_error"; slug: string; message: string };

export type AtlasAnalyticsClass =
  | "atlas_tail_rendered"
  | "atlas_not_found"
  | "atlas_fetch_failed";

export function analyticsClassForState(
  state: AtlasClientShellState,
): AtlasAnalyticsClass | null {
  switch (state.status) {
    case "ready":
      return "atlas_tail_rendered";
    case "not_found":
      return "atlas_not_found";
    case "corrupt":
    case "network_error":
      return "atlas_fetch_failed";
    case "loading":
      return null;
  }
}

function mapError(
  slug: string,
  error: unknown,
): Exclude<AtlasClientShellState, { status: "loading" }> {
  if (error instanceof AtlasDataSourceError) {
    if (error.code === "integrity_error" || error.code === "unsupported_schema") {
      return { status: "corrupt", slug, message: error.message };
    }
    if (error.code === "invalid_slug") {
      return { status: "not_found", slug };
    }
    // unavailable + version_mismatch → retryable network/fetch failure UI
    return { status: "network_error", slug, message: error.message };
  }
  return {
    status: "network_error",
    slug,
    message: error instanceof Error ? error.message : String(error),
  };
}

/**
 * Preflight against the public search index so unknown lemma 404 surfaces
 * never request `/atlas/current.json` (K3 B2).
 *
 * Returns `missing` when the index loads and the slug is absent; `unknown`
 * when the index is unavailable (caller falls through to HttpAtlasDataSource).
 */
export async function preflightAtlasSlugInSearchIndex(
  slug: string,
  fetchImpl: typeof fetch,
  baseUrl = "/",
  onIndexLoaded?: (rows: AtlasSearchArticleRow[]) => void,
): Promise<"found" | "missing" | "unknown"> {
  const url = absoluteSitePath("/lexicon/search-index.json", baseUrl);
  try {
    const response = await fetchImpl(url);
    if (!response.ok) return "unknown";
    const data: unknown = await response.json();
    if (!Array.isArray(data)) return "unknown";
    onIndexLoaded?.(data as AtlasSearchArticleRow[]);
    const hit = data.some(
      (row) =>
        row &&
        typeof row === "object" &&
        "s" in row &&
        typeof (row as { s: unknown }).s === "string" &&
        (row as { s: string }).s === slug,
    );
    return hit ? "found" : "missing";
  } catch {
    return "unknown";
  }
}

/** Load the public lexical catalog used for learner-facing Atlas backlinks. */
export async function loadAtlasLinkCatalog(
  fetchImpl: typeof fetch,
  baseUrl = "/",
  articleRows?: readonly AtlasSearchArticleRow[],
): Promise<AtlasLinkCatalog | null> {
  try {
    let articles = articleRows;
    if (!articles) {
      const response = await fetchImpl(
        absoluteSitePath("/lexicon/search-index.json", baseUrl),
      );
      if (!response.ok) return null;
      const data: unknown = await response.json();
      if (!Array.isArray(data)) return null;
      articles = data as AtlasSearchArticleRow[];
    }

    let aliases: AtlasSearchAliasRow[] = [];
    try {
      const response = await fetchImpl(
        absoluteSitePath("/lexicon/search-aliases.json", baseUrl),
      );
      if (response.ok) {
        const data: unknown = await response.json();
        if (Array.isArray(data)) aliases = data as AtlasSearchAliasRow[];
      }
    } catch {
      // Direct article heads still provide useful links when aliases are offline.
    }

    return buildAtlasLinkCatalogFromSearchRows(articles, aliases);
  } catch {
    return null;
  }
}

/**
 * Resolve a slug through any `AtlasDataSource` into a terminal shell state
 * (or throw never — all failures become typed states).
 */
export async function loadAtlasClientShellEntry(
  slug: string,
  source: AtlasDataSource,
  options?: { generatedAt?: string },
): Promise<Exclude<AtlasClientShellState, { status: "loading" }>> {
  try {
    const result = await source.getEntry(slug);
    if (result.kind === "missing") {
      return { status: "not_found", slug };
    }
    return {
      status: "ready",
      slug,
      record: result.record,
      manifestVersion: result.version,
      generatedAt: options?.generatedAt ?? result.version,
    };
  } catch (error) {
    return mapError(slug, error);
  }
}
