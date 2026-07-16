/**
 * HTTP Atlas data source — browser-portable reader for exported runtime shards.
 *
 * Production serves dictionary shards as GitHub Release assets fetched on demand
 * by the browser (client-rendered word pages). This module must stay free of
 * `node:*` imports. Node-only helpers (file fetch, gunzipSync) live in
 * `http-atlas-node.ts`.
 */

import {
  AtlasDataSourceError,
  isValidAtlasSlug,
  type AtlasDataSource,
  type DeckPart,
  type DeckResult,
  type EntryRecord,
  type EntryResult,
  type SearchResponse,
} from "./atlas-data-source.ts";
import { normalizeAtlasText, normalizeSlugForHash } from "./normalize.ts";
import { PRACTICE_LEVELS, type PracticeLevel } from "./runtime-contract.ts";
import { rankSearchResults, type SearchAlias, type SearchRow } from "./search.ts";
import type { PracticeDeckData } from "./srs.ts";

export interface AtlasFetch {
  (url: string): Promise<Uint8Array>;
}

/** Pluggable gzip decode — browsers use DecompressionStream; Node injects gunzipSync. */
export type AtlasDecompress = (compressed: Uint8Array) => Promise<Uint8Array> | Uint8Array;

export interface AtlasAssetBaseEnv {
  /** Vite public env: immutable raw.githubusercontent.com/.../<sha>/… overflow base (R7). */
  PUBLIC_ATLAS_ASSET_BASE_URL?: string;
}

export interface HttpAtlasDataSourceOptions {
  /**
   * Atlas asset root. Production default is same-origin `/atlas` (PR3 D1).
   * Overflow escape (R7, design-in): set `PUBLIC_ATLAS_ASSET_BASE_URL` at build
   * time to an immutable commit-SHA `raw.githubusercontent.com` URL — never a
   * branch name. Explicit option wins over env.
   */
  assetBaseUrl?: string;
  /**
   * Inject build-time env for tests / Node. Defaults to `import.meta.env` when
   * available. Only `PUBLIC_ATLAS_ASSET_BASE_URL` is read.
   */
  env?: AtlasAssetBaseEnv;
  /**
   * Max age for cached `current.json` / manifest pointer resolution.
   * Default 60s. Set to 0 to re-resolve on every logical request (tests).
   */
  pointerTtlMs?: number;
  /** Override gzip decode. Defaults to browser `DecompressionStream("gzip")`. */
  decompress?: AtlasDecompress;
  /** Clock for pointer TTL; injectable for tests. */
  now?: () => number;
}

/** Default pointer TTL — short enough to observe release rollovers, long enough to amortize fetches. */
export const DEFAULT_POINTER_TTL_MS = 60_000;

/** Same-origin Pages-vendored tree root (PR3 D1). */
export const DEFAULT_ATLAS_ASSET_BASE_URL = "/atlas";

/**
 * Resolve the Atlas asset base URL (R7 overflow hook).
 *
 * Precedence: explicit `assetBaseUrl` → `PUBLIC_ATLAS_ASSET_BASE_URL` →
 * `DEFAULT_ATLAS_ASSET_BASE_URL` (`/atlas`).
 *
 * For on-disk fixture fetchers that root at the `atlas/` directory, pass
 * `assetBaseUrl: ""` so relative paths stay unprefixed.
 */
export function resolveAtlasAssetBaseUrl(options?: {
  assetBaseUrl?: string;
  env?: AtlasAssetBaseEnv;
}): string {
  if (options && Object.prototype.hasOwnProperty.call(options, "assetBaseUrl")) {
    const explicit = options.assetBaseUrl ?? "";
    return explicit.replace(/\/$/, "");
  }
  const env = options?.env ?? readImportMetaEnv();
  const fromEnv = env?.PUBLIC_ATLAS_ASSET_BASE_URL?.trim();
  if (fromEnv) {
    return fromEnv.replace(/\/$/, "");
  }
  return DEFAULT_ATLAS_ASSET_BASE_URL;
}

/**
 * Constructor-time base resolution: env override when set, else explicit option,
 * else empty string (backward-compatible for Node fixture fetchers).
 * Product same-origin default `/atlas` is applied by the app shell / 404 page
 * (or by calling {@link resolveAtlasAssetBaseUrl} without an explicit base).
 */
function resolveConstructorAssetBaseUrl(options?: HttpAtlasDataSourceOptions): string {
  if (options && Object.prototype.hasOwnProperty.call(options, "assetBaseUrl")) {
    return (options.assetBaseUrl ?? "").replace(/\/$/, "");
  }
  const env = options?.env ?? readImportMetaEnv();
  const fromEnv = env?.PUBLIC_ATLAS_ASSET_BASE_URL?.trim();
  if (fromEnv) {
    return fromEnv.replace(/\/$/, "");
  }
  return "";
}

function readImportMetaEnv(): AtlasAssetBaseEnv | undefined {
  try {
    // Vite injects import.meta.env; guard for non-Vite Node unit contexts.
    const meta = import.meta as ImportMeta & { env?: AtlasAssetBaseEnv };
    return meta.env;
  } catch {
    return undefined;
  }
}

interface CurrentPointer {
  schema: string;
  schemaVersion: number;
  dataVersion: string;
  generatedAt: string;
  manifestUrl: string;
}

interface ObjectDescriptor {
  id: string;
  url: string;
  count: number;
  bytes: number;
  uncompressedBytes: number;
  sha256: string;
  jsonSha256: string;
  encoding: "gzip";
}

interface RuntimeManifest {
  schema: string;
  schemaVersion: number;
  dataVersion: string;
  generatedAt: string;
  entries: {
    tree: EntryTreeNode;
    shards: Record<string, ObjectDescriptor>;
  };
  search: {
    articles: SearchFamilyIndex;
    aliases: SearchFamilyIndex;
  };
  decks: {
    levels: Record<
      string,
      {
        deckVersion: string;
        parts: Record<string, ObjectDescriptor>;
      }
    >;
  };
}

interface EntryTreeNode {
  bitLength?: number;
  shardId?: string;
  children?: Record<string, EntryTreeNode>;
}

interface SearchFamilyIndex {
  tree: SearchTreeNode;
  shards: Record<string, ObjectDescriptor>;
}

interface SearchTreeNode {
  prefix?: string;
  shardId?: string;
  terminalShardId?: string;
  children?: Record<string, SearchTreeNode>;
}

/** Snapshot pinned for one logical request (getEntry / search / getDeck). */
interface PinnedAtlasSession {
  pointer: CurrentPointer;
  manifest: RuntimeManifest;
  versionDir: string;
}

/** Copy into a real ArrayBuffer-backed view (TS 5.7+/6 BufferSource strictness). */
function toArrayBufferView(data: Uint8Array): Uint8Array<ArrayBuffer> {
  const copy = new Uint8Array(data.byteLength);
  copy.set(data);
  return copy;
}

async function sha256Hex(data: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", toArrayBufferView(data));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function decodeJson<T>(raw: Uint8Array): T {
  return JSON.parse(new TextDecoder("utf-8").decode(raw)) as T;
}

/**
 * Browser-default gzip decode via the Compression Streams API.
 * Available in modern browsers and Node 20+.
 */
export async function gunzipWithDecompressionStream(compressed: Uint8Array): Promise<Uint8Array> {
  if (typeof DecompressionStream === "undefined") {
    throw new AtlasDataSourceError(
      "unavailable",
      "DecompressionStream is not available; inject options.decompress (e.g. Node gunzipSync)",
    );
  }
  const copy = toArrayBufferView(compressed);
  const stream = new Blob([copy]).stream().pipeThrough(new DecompressionStream("gzip"));
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

/**
 * Admit search article rows the ranker can score — lemma/roman exact·prefix and
 * gloss substring (mirrors `matchTier` surfaces used by SqliteAtlasDataSource).
 */
export function admitsSearchArticle(row: SearchRow, normalizedQuery: string): boolean {
  if (!normalizedQuery) return false;
  const lemma = normalizeAtlasText(row.l);
  const roman = row.r ? normalizeAtlasText(row.r) : "";
  const gloss = row.g ? normalizeAtlasText(row.g) : "";
  return (
    lemma === normalizedQuery ||
    lemma.startsWith(normalizedQuery) ||
    lemma.includes(normalizedQuery) ||
    (roman.length > 0 &&
      (roman === normalizedQuery ||
        roman.startsWith(normalizedQuery) ||
        roman.includes(normalizedQuery))) ||
    (gloss.length > 0 && gloss.includes(normalizedQuery))
  );
}

export class HttpAtlasDataSource implements AtlasDataSource {
  private current: CurrentPointer | null = null;
  private currentFetchedAt = 0;
  private manifest: RuntimeManifest | null = null;
  private versionDir = "";
  private readonly assetCache = new Map<string, Uint8Array>();
  private readonly assetBaseUrl: string;
  private readonly pointerTtlMs: number;
  private readonly decompress: AtlasDecompress;
  private readonly now: () => number;

  constructor(
    private readonly fetchBytes: AtlasFetch,
    private readonly options?: HttpAtlasDataSourceOptions,
  ) {
    // Env overflow hook (R7) when assetBaseUrl is omitted; explicit option wins.
    this.assetBaseUrl = resolveConstructorAssetBaseUrl(options);
    this.pointerTtlMs = options?.pointerTtlMs ?? DEFAULT_POINTER_TTL_MS;
    this.decompress = options?.decompress ?? gunzipWithDecompressionStream;
    this.now = options?.now ?? (() => Date.now());
  }

  private assetUrl(relative: string): string {
    const base = this.assetBaseUrl;
    if (!base) return relative;
    return `${base.replace(/\/$/, "")}/${relative.replace(/^\//, "")}`;
  }

  private pointerCacheFresh(force: boolean): boolean {
    if (force || !this.current) return false;
    return this.now() - this.currentFetchedAt < this.pointerTtlMs;
  }

  /**
   * Resolve (or re-resolve) current.json + matching manifest, then return a
   * request-pinned session so mid-request rollovers cannot tear shard URLs.
   */
  private async resolveSession(force = false): Promise<PinnedAtlasSession> {
    let pointer = this.current;
    if (!this.pointerCacheFresh(force)) {
      const raw = await this.fetchBytes(this.assetUrl("current.json"));
      pointer = decodeJson<CurrentPointer>(raw);
      if (pointer.schema !== "atlas-current" || pointer.schemaVersion !== 1) {
        throw new AtlasDataSourceError("unsupported_schema", "unsupported current.json schema");
      }
      this.current = pointer;
      this.currentFetchedAt = this.now();
    }
    if (!pointer) {
      throw new AtlasDataSourceError("unavailable", "current.json pointer missing after resolve");
    }

    const needsManifest =
      force || !this.manifest || this.manifest.dataVersion !== pointer.dataVersion;
    if (needsManifest) {
      const versionDir = pointer.manifestUrl.replace(/\/manifest\.json$/, "");
      const raw = await this.fetchBytes(this.assetUrl(pointer.manifestUrl));
      const manifest = decodeJson<RuntimeManifest>(raw);
      if (manifest.schema !== "atlas-runtime-manifest" || manifest.schemaVersion !== 1) {
        throw new AtlasDataSourceError("unsupported_schema", "unsupported manifest schema");
      }
      if (manifest.dataVersion !== pointer.dataVersion) {
        throw new AtlasDataSourceError(
          "version_mismatch",
          `current points to ${pointer.dataVersion} but manifest is ${manifest.dataVersion}`,
        );
      }
      this.manifest = manifest;
      this.versionDir = versionDir;
    }

    // Pin field copies for this request — concurrent resolveSession must not
    // mutate the versionDir/manifest this request is already using.
    return {
      pointer,
      manifest: this.manifest!,
      versionDir: this.versionDir,
    };
  }

  private async readObject(
    descriptor: ObjectDescriptor,
    expectedVersion: string,
    versionDir: string,
    options?: { kind?: "entry" | "search" | "deck" },
  ): Promise<unknown> {
    const url = `${versionDir}/${descriptor.url}`.replace(/\/+/g, "/");
    const cacheKey = `${expectedVersion}:${descriptor.id}:${descriptor.sha256}`;
    let compressed = this.assetCache.get(cacheKey);
    if (!compressed) {
      compressed = await this.fetchBytes(this.assetUrl(url.replace(/^\//, "")));
      this.assetCache.set(cacheKey, compressed);
    }
    if (compressed.byteLength !== descriptor.bytes) {
      throw new AtlasDataSourceError(
        "integrity_error",
        `byte length mismatch for ${descriptor.id}`,
      );
    }
    const compressedDigest = await sha256Hex(compressed);
    if (compressedDigest !== descriptor.sha256) {
      throw new AtlasDataSourceError("integrity_error", `sha256 mismatch for ${descriptor.id}`);
    }
    let raw: Uint8Array;
    try {
      raw = await this.decompress(compressed);
    } catch (error) {
      if (error instanceof AtlasDataSourceError) throw error;
      throw new AtlasDataSourceError(
        "integrity_error",
        `gzip decode failed for ${descriptor.id}: ${String(error)}`,
      );
    }
    if (raw.byteLength !== descriptor.uncompressedBytes) {
      throw new AtlasDataSourceError(
        "integrity_error",
        `uncompressedBytes mismatch for ${descriptor.id}`,
      );
    }
    const jsonDigest = await sha256Hex(raw);
    if (jsonDigest !== descriptor.jsonSha256) {
      throw new AtlasDataSourceError("integrity_error", `jsonSha256 mismatch for ${descriptor.id}`);
    }
    const payload = decodeJson<Record<string, unknown>>(raw);
    if (options?.kind === "deck") {
      return payload;
    }
    if (payload.schemaVersion !== 1) {
      throw new AtlasDataSourceError("unsupported_schema", `unsupported shard schema for ${descriptor.id}`);
    }
    if (typeof payload.dataVersion === "string" && payload.dataVersion !== expectedVersion) {
      throw new AtlasDataSourceError(
        "version_mismatch",
        `shard ${descriptor.id} version ${payload.dataVersion} != ${expectedVersion}`,
      );
    }
    return payload;
  }

  private async withVersionRetry<T>(
    expectedVersion: string | undefined,
    action: (session: PinnedAtlasSession) => Promise<T>,
  ): Promise<T> {
    const session = await this.resolveSession(false);
    if (expectedVersion && expectedVersion !== session.manifest.dataVersion) {
      throw new AtlasDataSourceError(
        "version_mismatch",
        `expected ${expectedVersion}, have ${session.manifest.dataVersion}`,
      );
    }
    try {
      return await action(session);
    } catch (error) {
      if (!(error instanceof AtlasDataSourceError) || error.code !== "version_mismatch") {
        throw error;
      }
      // Discard partials, refresh current.json, retry once.
      this.assetCache.clear();
      this.current = null;
      this.currentFetchedAt = 0;
      this.manifest = null;
      this.versionDir = "";
      const refreshed = await this.resolveSession(true);
      if (expectedVersion && expectedVersion !== refreshed.manifest.dataVersion) {
        throw error;
      }
      return action(refreshed);
    }
  }

  private async slugHashBits(slug: string): Promise<string> {
    const normalized = normalizeSlugForHash(slug);
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(normalized));
    return [...new Uint8Array(digest)].map((b) => b.toString(2).padStart(8, "0")).join("");
  }

  private resolveEntryShardId(tree: EntryTreeNode, bits: string): string {
    let node = tree;
    let depth = 0;
    while (!node.shardId) {
      const children = node.children;
      if (!children) {
        throw new AtlasDataSourceError("integrity_error", "entry trie missing shard leaf");
      }
      const bit = bits[depth];
      if (bit !== "0" && bit !== "1") {
        throw new AtlasDataSourceError("integrity_error", "hash bits exhausted before leaf");
      }
      const child = children[bit];
      if (!child) {
        throw new AtlasDataSourceError("integrity_error", `entry trie missing child bit=${bit}`);
      }
      node = child;
      depth += 1;
    }
    return node.shardId;
  }

  private collectSearchShardIds(node: SearchTreeNode, query: string, prefix = ""): string[] {
    const ids: string[] = [];
    if (node.terminalShardId) ids.push(node.terminalShardId);
    if (node.shardId) {
      ids.push(node.shardId);
      return ids;
    }
    const children = node.children ?? {};
    if (query.length <= prefix.length) {
      // Query ended on an internal node: terminal + all descendant leaves.
      const walk = (n: SearchTreeNode): void => {
        if (n.terminalShardId) ids.push(n.terminalShardId);
        if (n.shardId) ids.push(n.shardId);
        for (const child of Object.values(n.children ?? {})) walk(child);
      };
      walk(node);
      return [...new Set(ids)];
    }
    const next = query[prefix.length]!;
    const child = children[next];
    if (!child) {
      // No deeper child — return whatever terminal exists at this node.
      return [...new Set(ids)];
    }
    return this.collectSearchShardIds(child, query, prefix + next);
  }

  async getEntry(slug: string, options?: { expectedVersion?: string }): Promise<EntryResult> {
    if (!isValidAtlasSlug(slug)) {
      throw new AtlasDataSourceError("invalid_slug", `invalid slug: ${JSON.stringify(slug)}`);
    }
    return this.withVersionRetry(options?.expectedVersion, async (session) => {
      const { manifest, versionDir } = session;
      const bits = await this.slugHashBits(slug);
      const shardId = this.resolveEntryShardId(manifest.entries.tree, bits);
      const descriptor = manifest.entries.shards[shardId];
      if (!descriptor) {
        throw new AtlasDataSourceError("integrity_error", `missing entry shard descriptor ${shardId}`);
      }
      const payload = (await this.readObject(descriptor, manifest.dataVersion, versionDir)) as {
        records: EntryRecord[];
      };
      const record = payload.records.find((item) => item.slug === slug);
      if (!record) return { kind: "missing", version: manifest.dataVersion, slug };
      return { kind: "entry", version: manifest.dataVersion, record };
    });
  }

  async search(
    query: string,
    options?: { limit?: number; expectedVersion?: string },
  ): Promise<SearchResponse> {
    return this.withVersionRetry(options?.expectedVersion, async (session) => {
      const { manifest, versionDir } = session;
      const normalizedQuery = normalizeAtlasText(query);
      const limit = options?.limit ?? 12;
      if (!normalizedQuery) {
        return {
          version: manifest.dataVersion,
          normalizedQuery,
          results: [],
          truncated: false,
          fetchedShardIds: [],
        };
      }

      const articleIds = this.collectSearchShardIds(manifest.search.articles.tree, normalizedQuery);
      const aliasIds = this.collectSearchShardIds(manifest.search.aliases.tree, normalizedQuery);
      const fetchedShardIds = [
        ...articleIds.map((id) => `articles:${id}`),
        ...aliasIds.map((id) => `aliases:${id}`),
      ];

      const [articlePayloads, aliasPayloads] = await Promise.all([
        Promise.all(
          articleIds.map(async (id) => {
            const descriptor = manifest.search.articles.shards[id];
            if (!descriptor) {
              throw new AtlasDataSourceError("integrity_error", `missing article search shard ${id}`);
            }
            return this.readObject(descriptor, manifest.dataVersion, versionDir) as Promise<{
              records: SearchRow[];
            }>;
          }),
        ),
        Promise.all(
          aliasIds.map(async (id) => {
            const descriptor = manifest.search.aliases.shards[id];
            if (!descriptor) {
              throw new AtlasDataSourceError("integrity_error", `missing alias search shard ${id}`);
            }
            return this.readObject(descriptor, manifest.dataVersion, versionDir) as Promise<{
              records: SearchAlias[];
            }>;
          }),
        ),
      ]);

      const articlesBySlug = new Map<string, SearchRow>();
      for (const payload of articlePayloads) {
        for (const row of payload.records) {
          if (admitsSearchArticle(row, normalizedQuery)) {
            articlesBySlug.set(row.s, row);
          }
        }
      }
      const aliases: SearchAlias[] = [];
      const seenAlias = new Set<string>();
      for (const payload of aliasPayloads) {
        for (const row of payload.records) {
          const text = normalizeAtlasText(row.a);
          if (!(text === normalizedQuery || text.startsWith(normalizedQuery) || text.includes(normalizedQuery))) {
            continue;
          }
          const key = `${row.a}\0${row.s}\0${row.k}`;
          if (seenAlias.has(key)) continue;
          seenAlias.add(key);
          aliases.push(row);
        }
      }

      const ranked = rankSearchResults([...articlesBySlug.values()], aliases, query, limit + 1);
      const truncated = ranked.length > limit;
      return {
        version: manifest.dataVersion,
        normalizedQuery,
        results: ranked.slice(0, limit),
        truncated,
        fetchedShardIds,
      };
    });
  }

  async getDeck(
    level: PracticeLevel,
    options?: { parts?: DeckPart[]; expectedVersion?: string },
  ): Promise<DeckResult> {
    if (!PRACTICE_LEVELS.includes(level)) {
      throw new AtlasDataSourceError("invalid_slug", `invalid practice level ${level}`);
    }
    return this.withVersionRetry(options?.expectedVersion, async (session) => {
      const { manifest, versionDir } = session;
      const info = manifest.decks.levels[level];
      if (!info) return { kind: "missing", version: manifest.dataVersion, level };
      const parts = options?.parts ?? (["index", "lexemes", "cloze"] as DeckPart[]);
      const loaded: Partial<Record<DeckPart, unknown>> = {};
      const versions = new Set<string>();
      for (const part of parts) {
        const descriptor = info.parts[part];
        if (!descriptor) return { kind: "missing", version: manifest.dataVersion, level };
        const payload = (await this.readObject(descriptor, manifest.dataVersion, versionDir, {
          kind: "deck",
        })) as {
          deckVersion?: string;
          items?: unknown[];
          lexemes?: unknown[];
          cloze?: unknown[];
        };
        if (typeof payload.deckVersion === "string") versions.add(payload.deckVersion);
        loaded[part] = payload;
      }
      if (versions.size !== 1 || !versions.has(info.deckVersion)) {
        throw new AtlasDataSourceError(
          "integrity_error",
          `deck parts for ${level} do not share deckVersion ${info.deckVersion}`,
        );
      }
      const indexPart = loaded.index as { items?: PracticeDeckData["index"] } | undefined;
      const lexemesPart = loaded.lexemes as { lexemes?: PracticeDeckData["lexemes"] } | undefined;
      const clozePart = loaded.cloze as { cloze?: PracticeDeckData["cloze"] } | undefined;
      const data: PracticeDeckData = {
        deckVersion: info.deckVersion,
        level,
        index: indexPart?.items ?? [],
        lexemes: lexemesPart?.lexemes ?? [],
        cloze: clozePart?.cloze ?? [],
      };
      return {
        kind: "deck",
        version: manifest.dataVersion,
        deckVersion: info.deckVersion,
        level,
        data,
      };
    });
  }
}
