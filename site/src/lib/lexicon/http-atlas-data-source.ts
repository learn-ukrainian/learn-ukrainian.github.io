/**
 * HTTP/file Atlas data source — reads an exported runtime shard tree.
 *
 * Used for parity tests against SqliteAtlasDataSource and as the browser/VPS
 * reader shape. R2AtlasDataSource (Worker binding + Cache API) is a later PR.
 */

import { gunzipSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
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

async function sha256Hex(data: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function decodeJson<T>(raw: Uint8Array): T {
  return JSON.parse(new TextDecoder("utf-8").decode(raw)) as T;
}

export function createFileAtlasFetch(rootDir: string, basePath = "atlas"): AtlasFetch {
  const root = resolve(rootDir, basePath);
  return async (url: string) => {
    const path = resolve(root, url);
    if (!path.startsWith(root)) {
      throw new AtlasDataSourceError("invalid_slug", `refusing path escape: ${url}`);
    }
    try {
      return new Uint8Array(readFileSync(path));
    } catch (error) {
      throw new AtlasDataSourceError("unavailable", `failed to read ${url}: ${String(error)}`);
    }
  };
}

export class HttpAtlasDataSource implements AtlasDataSource {
  private current: CurrentPointer | null = null;
  private manifest: RuntimeManifest | null = null;
  private readonly assetCache = new Map<string, Uint8Array>();

  constructor(
    private readonly fetchBytes: AtlasFetch,
    private readonly options?: { assetBaseUrl?: string },
  ) {}

  private assetUrl(relative: string): string {
    const base = this.options?.assetBaseUrl ?? "";
    if (!base) return relative;
    return `${base.replace(/\/$/, "")}/${relative.replace(/^\//, "")}`;
  }

  private async loadCurrent(force = false): Promise<CurrentPointer> {
    if (this.current && !force) return this.current;
    const raw = await this.fetchBytes(this.assetUrl("current.json"));
    const pointer = decodeJson<CurrentPointer>(raw);
    if (pointer.schema !== "atlas-current" || pointer.schemaVersion !== 1) {
      throw new AtlasDataSourceError("unsupported_schema", "unsupported current.json schema");
    }
    this.current = pointer;
    return pointer;
  }

  private async loadManifest(force = false): Promise<RuntimeManifest> {
    if (this.manifest && !force) return this.manifest;
    const current = await this.loadCurrent(force);
    const versionDir = current.manifestUrl.replace(/\/manifest\.json$/, "");
    const raw = await this.fetchBytes(this.assetUrl(current.manifestUrl));
    const manifest = decodeJson<RuntimeManifest>(raw);
    if (manifest.schema !== "atlas-runtime-manifest" || manifest.schemaVersion !== 1) {
      throw new AtlasDataSourceError("unsupported_schema", "unsupported manifest schema");
    }
    if (manifest.dataVersion !== current.dataVersion) {
      throw new AtlasDataSourceError(
        "version_mismatch",
        `current points to ${current.dataVersion} but manifest is ${manifest.dataVersion}`,
      );
    }
    // Bind relative shard URLs against the version directory.
    this.manifest = manifest;
    this.manifestVersionDir = versionDir;
    return manifest;
  }

  private manifestVersionDir = "";

  private async readObject(
    descriptor: ObjectDescriptor,
    expectedVersion: string,
    options?: { kind?: "entry" | "search" | "deck" },
  ): Promise<unknown> {
    const url = `${this.manifestVersionDir}/${descriptor.url}`.replace(/\/+/g, "/");
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
      raw = gunzipSync(compressed);
    } catch (error) {
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
    action: (manifest: RuntimeManifest) => Promise<T>,
  ): Promise<T> {
    const manifest = await this.loadManifest(false);
    if (expectedVersion && expectedVersion !== manifest.dataVersion) {
      throw new AtlasDataSourceError(
        "version_mismatch",
        `expected ${expectedVersion}, have ${manifest.dataVersion}`,
      );
    }
    try {
      return await action(manifest);
    } catch (error) {
      if (!(error instanceof AtlasDataSourceError) || error.code !== "version_mismatch") {
        throw error;
      }
      // Discard partials, refresh current.json, retry once.
      this.assetCache.clear();
      this.current = null;
      this.manifest = null;
      const refreshed = await this.loadManifest(true);
      if (expectedVersion && expectedVersion !== refreshed.dataVersion) {
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
    return this.withVersionRetry(options?.expectedVersion, async (manifest) => {
      const bits = await this.slugHashBits(slug);
      const shardId = this.resolveEntryShardId(manifest.entries.tree, bits);
      const descriptor = manifest.entries.shards[shardId];
      if (!descriptor) {
        throw new AtlasDataSourceError("integrity_error", `missing entry shard descriptor ${shardId}`);
      }
      const payload = (await this.readObject(descriptor, manifest.dataVersion)) as {
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
    return this.withVersionRetry(options?.expectedVersion, async (manifest) => {
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
            return this.readObject(descriptor, manifest.dataVersion) as Promise<{
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
            return this.readObject(descriptor, manifest.dataVersion) as Promise<{
              records: SearchAlias[];
            }>;
          }),
        ),
      ]);

      const articlesBySlug = new Map<string, SearchRow>();
      for (const payload of articlePayloads) {
        for (const row of payload.records) {
          const lemma = normalizeAtlasText(row.l);
          const roman = row.r ? normalizeAtlasText(row.r) : "";
          if (
            lemma === normalizedQuery ||
            lemma.startsWith(normalizedQuery) ||
            roman.startsWith(normalizedQuery)
          ) {
            articlesBySlug.set(row.s, row);
          }
        }
      }
      const aliases: SearchAlias[] = [];
      const seenAlias = new Set<string>();
      for (const payload of aliasPayloads) {
        for (const row of payload.records) {
          const text = normalizeAtlasText(row.a);
          if (!(text === normalizedQuery || text.startsWith(normalizedQuery))) continue;
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
    return this.withVersionRetry(options?.expectedVersion, async (manifest) => {
      const info = manifest.decks.levels[level];
      if (!info) return { kind: "missing", version: manifest.dataVersion, level };
      const parts = options?.parts ?? (["index", "lexemes", "cloze"] as DeckPart[]);
      const loaded: Partial<Record<DeckPart, unknown>> = {};
      const versions = new Set<string>();
      for (const part of parts) {
        const descriptor = info.parts[part];
        if (!descriptor) return { kind: "missing", version: manifest.dataVersion, level };
        const payload = (await this.readObject(descriptor, manifest.dataVersion, {
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
