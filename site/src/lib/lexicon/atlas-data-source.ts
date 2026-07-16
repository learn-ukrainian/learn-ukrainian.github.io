/**
 * Versioned Atlas runtime data-source contract (PR #1 foundation).
 *
 * Http/R2 edge readers land in later PRs; this module defines the shared
 * types plus typed failures. SqliteAtlasDataSource is the SSG/parity baseline.
 */

import type { LexiconEntry } from "./atlasDb";
import type { PracticeLevel } from "./runtime-contract";
import type { PracticeDeckData } from "./srs";
import type { SearchAlias, SearchResult, SearchRow } from "./search";

export type EntryKind = "article" | "form_route";

export interface PublicAlias {
  alias: string;
  kind: string;
  source: string | null;
  target_slug: string;
}

export interface PublicRelation {
  related_slug: string;
  entry_type: string | null;
  relation: string;
  component_role: string | null;
  provenance: string;
}

export interface ArticleProvenance {
  source_family: string | null;
  source_locator: string | null;
  extraction_mode: string | null;
}

export interface ComponentLink {
  text: string;
  targetSlug: string | null;
}

export interface EntryRenderContext {
  componentLinks: ComponentLink[];
  practiceLevels: PracticeLevel[];
}

export interface EntryRecord {
  slug: string;
  kind: EntryKind;
  entry: LexiconEntry;
  aliases: PublicAlias[];
  relations: PublicRelation[];
  provenance: ArticleProvenance[];
  renderContext: EntryRenderContext;
}

export type EntryResult =
  | { kind: "entry"; version: string; record: EntryRecord }
  | { kind: "missing"; version: string; slug: string };

export type ArticleSearchRow = {
  l: string;
  s: string;
  g: string | null;
  r: string;
  t: string;
  c?: string;
  cls?: string;
};

export type AliasSearchRow = {
  a: string;
  k: string;
  s: string;
  h: string;
};

export interface SearchResponse {
  version: string;
  normalizedQuery: string;
  results: SearchResult[];
  truncated: boolean;
  fetchedShardIds: string[];
}

export type DeckPart = "index" | "lexemes" | "cloze";

export type DeckResult =
  | { kind: "deck"; version: string; deckVersion: string; level: PracticeLevel; data: PracticeDeckData }
  | { kind: "missing"; version: string; level: PracticeLevel };

export type AtlasDataSourceErrorCode =
  | "invalid_slug"
  | "version_mismatch"
  | "unsupported_schema"
  | "integrity_error"
  | "unavailable";

export class AtlasDataSourceError extends Error {
  readonly code: AtlasDataSourceErrorCode;
  readonly retryable: boolean;
  readonly httpStatus: number;

  constructor(code: AtlasDataSourceErrorCode, message: string) {
    super(message);
    this.name = "AtlasDataSourceError";
    this.code = code;
    switch (code) {
      case "invalid_slug":
        this.retryable = false;
        this.httpStatus = 400;
        break;
      case "version_mismatch":
        this.retryable = true;
        this.httpStatus = 409;
        break;
      case "unsupported_schema":
      case "integrity_error":
        this.retryable = false;
        this.httpStatus = 503;
        break;
      case "unavailable":
        this.retryable = true;
        this.httpStatus = 503;
        break;
    }
  }
}

export interface AtlasDataSource {
  getEntry(slug: string, options?: { expectedVersion?: string }): Promise<EntryResult>;
  search(
    query: string,
    options?: { limit?: number; expectedVersion?: string },
  ): Promise<SearchResponse>;
  getDeck(
    level: PracticeLevel,
    options?: { parts?: DeckPart[]; expectedVersion?: string },
  ): Promise<DeckResult>;
}

export function isValidAtlasSlug(slug: string): boolean {
  if (!slug || slug !== slug.normalize("NFC")) return false;
  if (slug.includes("/") || slug.includes("\\") || slug.includes("\0")) return false;
  if (slug !== slug.trim()) return false;
  return true;
}

export type { SearchRow, SearchAlias, SearchResult, LexiconEntry, PracticeLevel, PracticeDeckData };
