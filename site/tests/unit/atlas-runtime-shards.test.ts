// @vitest-environment node

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";
import { normalizeAtlasText } from "@site/src/lib/lexicon/normalize";
import {
  admitsSearchArticle,
  type AtlasFetch,
} from "@site/src/lib/lexicon/http-atlas-data-source";
import {
  createFileAtlasFetch,
  createNodeHttpAtlasDataSource,
} from "@site/src/lib/lexicon/http-atlas-node";
import {
  COMPONENT_TOKEN_RE,
  resetSqliteAtlasDataSourceCachesForTests,
  SqliteAtlasDataSource,
} from "@site/src/lib/lexicon/sqlite-atlas-data-source";
import { AtlasDataSourceError } from "@site/src/lib/lexicon/atlas-data-source";
import { rankSearchResults, type SearchRow } from "@site/src/lib/lexicon/search";
import reactRenderer from "@astrojs/react/server.js";
import { experimental_AstroContainer as AstroContainer } from "astro/container";
import {
  getAtlasPayloadCache,
  resetAtlasPayloadCacheForTests,
} from "@site/src/lib/lexicon/atlasDb";
import { gzipSync } from "node:zlib";
import { mkdtempSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { spawnSync } from "node:child_process";

const vectorsPath = resolve(
  process.cwd(),
  "../scripts/atlas/normalization_vectors.json",
);
const exportRoot = resolve(process.cwd(), "../build/atlas-runtime");
const atlasDbPath = resolve(process.cwd(), "../data/atlas.db");
const fixtureDbPath = resolve(
  process.cwd(),
  "../tests/fixtures/atlas/runtime_shards_fixture.db",
);
const hasAtlasDb = existsSync(atlasDbPath);
const hasExportRoot = existsSync(resolve(exportRoot, "atlas/current.json"));
const hasFixtureDb = existsSync(fixtureDbPath);

function nodeHttp(fetchBytes: AtlasFetch, options?: { pointerTtlMs?: number; now?: () => number }) {
  return createNodeHttpAtlasDataSource(fetchBytes, options);
}

const FIXTURE_SLUGS = [
  "прапор", // rich lemma
  "файний", // heritage warning
  "будь-ласка", // multiword / component links
  "доконаний-вид", // marked morphology / multiword
  "ілля", // proper name / entry type
  "іване", // form_of
];

const componentTokenVectorsPath = resolve(
  process.cwd(),
  "../scripts/atlas/component_tokenization_vectors.json",
);

describe("atlas normalization vectors", () => {
  test("TypeScript normalizeAtlasText matches shared vectors", () => {
    const payload = JSON.parse(readFileSync(vectorsPath, "utf-8")) as {
      cases: Array<{ input: string; expected: string }>;
    };
    for (const testCase of payload.cases) {
      expect(normalizeAtlasText(testCase.input), testCase.input).toBe(testCase.expected);
    }
  });
});

describe("atlas component tokenization vectors", () => {
  test("TypeScript COMPONENT_TOKEN_RE matches shared vectors", () => {
    const payload = JSON.parse(readFileSync(componentTokenVectorsPath, "utf-8")) as {
      cases: Array<{ id: string; input: string; expected: string[] }>;
    };
    for (const testCase of payload.cases) {
      expect(testCase.input.match(COMPONENT_TOKEN_RE) ?? [], testCase.id).toEqual(
        testCase.expected,
      );
    }
  });
});

describe("AtlasDataSource runtime shards", () => {
  test.skipIf(!hasAtlasDb || !hasExportRoot)(
    "Sqlite and Http entry records match for parity fixtures",
    async () => {
      resetAtlasPayloadCacheForTests();
      resetSqliteAtlasDataSourceCachesForTests();
      const sqlite = new SqliteAtlasDataSource();
      const http = nodeHttp(createFileAtlasFetch(exportRoot));

      for (const slug of FIXTURE_SLUGS) {
        const left = await sqlite.getEntry(slug);
        const right = await http.getEntry(slug);
        expect(left.kind, slug).toBe("entry");
        expect(right.kind, slug).toBe("entry");
        if (left.kind !== "entry" || right.kind !== "entry") continue;
        expect(right.record.entry).toEqual(left.record.entry);
        expect(right.record.kind).toBe(left.record.kind);
        expect(right.record.renderContext.componentLinks).toEqual(
          left.record.renderContext.componentLinks,
        );
      }
    },
  );

  test.skipIf(!hasAtlasDb || !hasExportRoot)(
    "WordAtlasArticle HTML is byte-identical across Sqlite vs Http entries",
    async () => {
      resetAtlasPayloadCacheForTests();
      resetSqliteAtlasDataSourceCachesForTests();
      const cache = getAtlasPayloadCache();
      const sqlite = new SqliteAtlasDataSource();
      const http = nodeHttp(createFileAtlasFetch(exportRoot));
      const { default: WordAtlasArticle } = await import(
        "@site/src/lexicon/WordAtlasArticle.astro"
      );
      const container = await AstroContainer.create();
      container.addServerRenderer({ renderer: reactRenderer });

      const entryTypes = new Set<string>();
      for (const entry of cache.entries) {
        if (entry.entry_type) entryTypes.add(entry.entry_type);
      }
      const byType = [...entryTypes].map((entryType) => {
        const hit = cache.entries.find((entry) => entry.entry_type === entryType);
        return hit!.url_slug;
      });
      const slugs = [...new Set([...FIXTURE_SLUGS, ...byType])];

      let differing = 0;
      for (const slug of slugs) {
        const left = await sqlite.getEntry(slug);
        const right = await http.getEntry(slug);
        expect(left.kind).toBe("entry");
        expect(right.kind).toBe("entry");
        if (left.kind !== "entry" || right.kind !== "entry") continue;

        const sqliteHtml = await container.renderToString(WordAtlasArticle, {
          props: {
            record: left.record,
            generatedAt: cache.generatedAt,
            manifestVersion: cache.manifestVersion,
          },
        });
        const httpHtml = await container.renderToString(WordAtlasArticle, {
          props: {
            record: right.record,
            generatedAt: cache.generatedAt,
            manifestVersion: cache.manifestVersion,
          },
        });
        if (sqliteHtml !== httpHtml) {
          differing += 1;
          throw new Error(`render parity failed for ${slug}`);
        }
      }
      process.stdout.write(
        `atlas datasource render parity: fixtures=${slugs.length} differing=${differing}\n`,
      );
      expect(differing).toBe(0);
    },
  );

  test.skipIf(!hasExportRoot)(
    "search exact/prefix fixtures match legacy ranker and keep families separate",
    async () => {
      const http = nodeHttp(createFileAtlasFetch(exportRoot));
      const articles = JSON.parse(
        readFileSync(resolve(process.cwd(), "src/data/lexicon-search-index.json"), "utf-8"),
      );
      const aliases = JSON.parse(
        readFileSync(resolve(process.cwd(), "src/data/lexicon-search-aliases.json"), "utf-8"),
      );

      // At scale, supported matching is exact/prefix over indexed keys. Filter the
      // legacy full-index ranker to the same contract so shard resolution is what
      // we assert — not legacy substring-across-corpus hits from other initials.
      const prefixOnly = (query: string) => {
        const nq = normalizeAtlasText(query);
        const articlePool = articles.filter((row: { l: string; r?: string }) => {
          const lemma = normalizeAtlasText(row.l);
          const roman = row.r ? normalizeAtlasText(row.r) : "";
          return lemma === nq || lemma.startsWith(nq) || roman.startsWith(nq);
        });
        const aliasPool = aliases.filter((row: { a: string }) => {
          const text = normalizeAtlasText(row.a);
          return text === nq || text.startsWith(nq);
        });
        return rankSearchResults(articlePool, aliasPool, query, 12);
      };

      for (const query of ["прапор", "фай", "іван"]) {
        const legacy = prefixOnly(query);
        const response = await http.search(query, { limit: 12 });
        expect(response.results.map((item) => item.article.s)).toEqual(
          legacy.map((item) => item.article.s),
        );
        expect(response.fetchedShardIds.some((id) => id.startsWith("articles:"))).toBe(true);
        expect(response.fetchedShardIds.every((id) => id.startsWith("articles:") || id.startsWith("aliases:"))).toBe(
          true,
        );
      }
    },
  );

  test.skipIf(!hasExportRoot)("version mismatch never combines two manifests", async () => {
    const http = nodeHttp(createFileAtlasFetch(exportRoot));
    await expect(http.getEntry("прапор", { expectedVersion: "atlas-v1-deadbeefdeadbeef" })).rejects.toBeInstanceOf(
      AtlasDataSourceError,
    );
    try {
      await http.getEntry("прапор", { expectedVersion: "atlas-v1-deadbeefdeadbeef" });
    } catch (error) {
      expect(error).toBeInstanceOf(AtlasDataSourceError);
      expect((error as AtlasDataSourceError).code).toBe("version_mismatch");
    }
  });

  test.skipIf(!hasExportRoot)("deck parts share one deckVersion", async () => {
    const http = nodeHttp(createFileAtlasFetch(exportRoot));
    const deck = await http.getDeck("A1");
    expect(deck.kind).toBe("deck");
    if (deck.kind !== "deck") return;
    expect(deck.deckVersion.length).toBeGreaterThan(0);
    expect(deck.data.deckVersion).toBe(deck.deckVersion);
  });

  test.skipIf(!hasExportRoot)("one-byte corruption fails closed", async () => {
    const current = JSON.parse(
      readFileSync(resolve(exportRoot, "atlas/current.json"), "utf-8"),
    ) as { dataVersion: string; manifestUrl: string };
    const versionDir = resolve(exportRoot, "atlas", current.manifestUrl.replace(/manifest\.json$/, ""));
    const manifest = JSON.parse(
      readFileSync(resolve(exportRoot, "atlas", current.manifestUrl), "utf-8"),
    ) as {
      entries: { shards: Record<string, { id: string; url: string; sha256: string }> };
    };

    // Locate the leaf that actually holds прапор, then corrupt that object.
    const httpProbe = nodeHttp(createFileAtlasFetch(exportRoot));
    const before = await httpProbe.getEntry("прапор");
    expect(before.kind).toBe("entry");

    // Hash walk to the shard id using the same algorithm as the reader.
    const slug = "прапор";
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(slug.normalize("NFC")));
    const bits = [...new Uint8Array(digest)].map((b) => b.toString(2).padStart(8, "0")).join("");
    let node: {
      shardId?: string;
      children?: Record<string, { shardId?: string; children?: Record<string, unknown> }>;
    } = (
      JSON.parse(readFileSync(resolve(exportRoot, "atlas", current.manifestUrl), "utf-8")) as {
        entries: { tree: { shardId?: string; children?: Record<string, unknown> } };
      }
    ).entries.tree;
    let depth = 0;
    while (!node.shardId) {
      const bit = bits[depth]!;
      node = node.children![bit]! as typeof node;
      depth += 1;
    }
    const descriptor = manifest.entries.shards[node.shardId!]!;
    const shardPath = resolve(versionDir, descriptor.url);
    const original = readFileSync(shardPath);
    const corrupted = Buffer.from(original);
    corrupted[0] = (corrupted[0] + 1) % 256;
    writeFileSync(shardPath, corrupted);
    const http = nodeHttp(createFileAtlasFetch(exportRoot));
    try {
      await expect(http.getEntry("прапор")).rejects.toBeInstanceOf(AtlasDataSourceError);
    } finally {
      writeFileSync(shardPath, original);
    }
  });
});

// ---------------------------------------------------------------------------
// Hermetic Sol F003 / F004 / F005 coverage (committed fixture export — always on)
// ---------------------------------------------------------------------------

async function sha256HexBuf(data: Uint8Array): Promise<string> {
  const copy = new Uint8Array(data.byteLength);
  copy.set(data);
  const digest = await crypto.subtle.digest("SHA-256", copy);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

describe("HttpAtlasDataSource Sol F003/F004/F005 (hermetic)", () => {
  test("admitsSearchArticle includes gloss-only hits (F005 unit)", () => {
    const row: SearchRow = {
      l: "достовірний",
      s: "достовірний",
      g: "reliable, trustworthy",
      r: "dostovirnyy",
    };
    expect(admitsSearchArticle(row, normalizeAtlasText("trustworthy"))).toBe(true);
    expect(admitsSearchArticle(row, normalizeAtlasText("достовірний"))).toBe(true);
    expect(admitsSearchArticle(row, normalizeAtlasText("zzzz-nope"))).toBe(false);
  });

  test("pointer rollover v1→v2 on reused instance; in-flight request pins version (F003)", async () => {
    const v1 = "atlas-v1-aaaaaaaaaaaaaaaa";
    const v2 = "atlas-v1-bbbbbbbbbbbbbbbb";
    const slug = "alpha";

    const entryV1 = {
      schema: "atlas-entry-shard",
      schemaVersion: 1,
      dataVersion: v1,
      records: [
        {
          slug,
          kind: "article",
          entry: { lemma: "alpha-v1", url_slug: slug },
          aliases: [],
          relations: [],
          provenance: [],
          renderContext: { componentLinks: [], practiceLevels: [] },
        },
      ],
    };
    const entryV2 = {
      ...entryV1,
      dataVersion: v2,
      records: [
        {
          ...entryV1.records[0],
          entry: { lemma: "alpha-v2", url_slug: slug },
        },
      ],
    };

    async function entryObject(payload: typeof entryV1, id: string, url: string) {
      const raw = Buffer.from(`${JSON.stringify(payload)}\n`, "utf-8");
      const compressed = new Uint8Array(gzipSync(raw, { level: 9 }));
      return {
        descriptor: {
          id,
          url,
          count: 1,
          bytes: compressed.byteLength,
          uncompressedBytes: raw.byteLength,
          sha256: await sha256HexBuf(compressed),
          jsonSha256: await sha256HexBuf(raw),
          encoding: "gzip" as const,
        },
        bytes: compressed,
      };
    }

    const shardV1 = await entryObject(entryV1, "e0", "entries/e0.json.gz");
    const shardV2 = await entryObject(entryV2, "e0", "entries/e0.json.gz");

    // Fixed hash leaf — any slug resolves to the single shard.
    const entryTree = { shardId: "e0" };

    function manifestFor(
      version: string,
      shard: { descriptor: Record<string, unknown> },
    ) {
      return {
        schema: "atlas-runtime-manifest",
        schemaVersion: 1,
        dataVersion: version,
        generatedAt: "2026-01-01T00:00:00+00:00",
        entries: {
          tree: entryTree,
          shards: { e0: shard.descriptor },
        },
        search: {
          articles: { tree: { shardId: "s0" }, shards: {} },
          aliases: { tree: { shardId: "a0" }, shards: {} },
        },
        decks: { levels: {} },
      };
    }

    const files = new Map<string, Uint8Array>([
      [
        "current.json",
        new TextEncoder().encode(
          JSON.stringify({
            schema: "atlas-current",
            schemaVersion: 1,
            dataVersion: v1,
            generatedAt: "2026-01-01T00:00:00+00:00",
            manifestUrl: `versions/${v1}/manifest.json`,
          }),
        ),
      ],
      [
        `versions/${v1}/manifest.json`,
        new TextEncoder().encode(JSON.stringify(manifestFor(v1, shardV1))),
      ],
      [`versions/${v1}/entries/e0.json.gz`, shardV1.bytes],
      [
        `versions/${v2}/manifest.json`,
        new TextEncoder().encode(JSON.stringify(manifestFor(v2, shardV2))),
      ],
      [`versions/${v2}/entries/e0.json.gz`, shardV2.bytes],
    ]);

    let clock = 1_000_000;

    const fetchStub: AtlasFetch = async (url) => {
      const bytes = files.get(url);
      if (!bytes) throw new AtlasDataSourceError("unavailable", `missing ${url}`);
      return bytes;
    };

    const http = nodeHttp(fetchStub, {
      pointerTtlMs: 60_000,
      now: () => clock,
    });

    const first = await http.getEntry(slug);
    expect(first.kind).toBe("entry");
    if (first.kind === "entry") {
      expect(first.version).toBe(v1);
      expect(first.record.entry.lemma).toBe("alpha-v1");
    }

    // Rollover current.json to v2; within TTL the instance would stay stale —
    // advance clock past TTL so the next request re-resolves the pointer.
    files.set(
      "current.json",
      new TextEncoder().encode(
        JSON.stringify({
          schema: "atlas-current",
          schemaVersion: 1,
          dataVersion: v2,
          generatedAt: "2026-01-02T00:00:00+00:00",
          manifestUrl: `versions/${v2}/manifest.json`,
        }),
      ),
    );
    clock += 60_001;

    const second = await http.getEntry(slug);
    expect(second.kind).toBe("entry");
    if (second.kind === "entry") {
      expect(second.version).toBe(v2);
      expect(second.record.entry.lemma).toBe("alpha-v2");
    }

    // Concurrent pin: start a request on v2, flip pointer mid-flight to a fake v3
    // that has no shards — the in-flight request must still finish on v2 URLs only.
    let releaseShard!: () => void;
    const shardGate = new Promise<void>((resolveGate) => {
      releaseShard = resolveGate;
    });
    const fetchedDuringPin: string[] = [];
    let v2ShardSeen = false;
    const pinFetch: AtlasFetch = async (url) => {
      fetchedDuringPin.push(url);
      if (url === `versions/${v2}/entries/e0.json.gz` && !v2ShardSeen) {
        v2ShardSeen = true;
        await shardGate;
      }
      const bytes = files.get(url);
      if (!bytes) throw new AtlasDataSourceError("unavailable", `missing ${url}`);
      return bytes;
    };
    // pointerTtlMs: 0 re-resolves current every request; pin still holds for in-flight.
    // Ensure current still points at v2 before the gated request starts.
    files.set(
      "current.json",
      new TextEncoder().encode(
        JSON.stringify({
          schema: "atlas-current",
          schemaVersion: 1,
          dataVersion: v2,
          generatedAt: "2026-01-02T00:00:00+00:00",
          manifestUrl: `versions/${v2}/manifest.json`,
        }),
      ),
    );
    const pinned = nodeHttp(pinFetch, { pointerTtlMs: 0, now: () => clock });
    const inflight = pinned.getEntry(slug);
    // Wait until the gated shard fetch is in flight (session already pinned to v2).
    for (let i = 0; i < 100 && !v2ShardSeen; i += 1) {
      await new Promise((r) => setTimeout(r, 2));
    }
    expect(v2ShardSeen).toBe(true);

    files.set(
      "current.json",
      new TextEncoder().encode(
        JSON.stringify({
          schema: "atlas-current",
          schemaVersion: 1,
          dataVersion: "atlas-v1-cccccccccccccccc",
          generatedAt: "2026-01-03T00:00:00+00:00",
          manifestUrl: "versions/atlas-v1-cccccccccccccccc/manifest.json",
        }),
      ),
    );
    releaseShard();
    const pinnedResult = await inflight;
    expect(pinnedResult.kind).toBe("entry");
    if (pinnedResult.kind === "entry") {
      expect(pinnedResult.version).toBe(v2);
      expect(pinnedResult.record.entry.lemma).toBe("alpha-v2");
    }
    // In-flight must not have fetched any v3 asset.
    expect(fetchedDuringPin.some((u) => u.includes("cccccccccccccccc"))).toBe(false);
    expect(fetchedDuringPin.some((u) => u.includes(v2))).toBe(true);
  });

  test("gloss-only query matches SqliteAtlasDataSource over fixture export (F005)", async () => {
    expect(hasFixtureDb).toBe(true);

    const outDir = mkdtempSync(resolve(tmpdir(), "atlas-fixture-export-"));
    try {
      const pySnippet = [
        "from pathlib import Path",
        "from scripts.atlas.export_runtime_shards import export_runtime_shards",
        `export_runtime_shards(db_path=Path(${JSON.stringify(fixtureDbPath)}), out_dir=Path(${JSON.stringify(outDir)}), include_decks=False, deck_dir=None, verify=True)`,
      ].join("; ");
      const exportResult = spawnSync(
        resolve(process.cwd(), "../.venv/bin/python"),
        ["-c", pySnippet],
        {
          cwd: resolve(process.cwd(), ".."),
          encoding: "utf-8",
          maxBuffer: 20 * 1024 * 1024,
        },
      );
      if (exportResult.status !== 0) {
        throw new Error(
          `fixture export failed: ${exportResult.stderr || exportResult.stdout || exportResult.status}`,
        );
      }

      const glossQuery = "trustworthy"; // distinctive: only in достовірний gloss, not lemma/roman
      const http = nodeHttp(createFileAtlasFetch(outDir), { pointerTtlMs: 0 });

      // Isolate Sqlite to fixture DB by temporarily hiding dual-publication search artifacts
      // so it projects search rows from the same fixture DB the export used.
      const searchIndex = resolve(process.cwd(), "src/data/lexicon-search-index.json");
      const searchAliases = resolve(process.cwd(), "src/data/lexicon-search-aliases.json");
      const bakIndex = `${searchIndex}.f005-bak`;
      const bakAliases = `${searchAliases}.f005-bak`;
      const prevAtlasDb = process.env.ATLAS_DB_PATH;
      let movedIndex = false;
      let movedAliases = false;
      try {
        if (existsSync(searchIndex)) {
          renameSync(searchIndex, bakIndex);
          movedIndex = true;
        }
        if (existsSync(searchAliases)) {
          renameSync(searchAliases, bakAliases);
          movedAliases = true;
        }
        process.env.ATLAS_DB_PATH = fixtureDbPath;
        resetSqliteAtlasDataSourceCachesForTests();
        resetAtlasPayloadCacheForTests();
        const sqlite = new SqliteAtlasDataSource();

        const left = await sqlite.search(glossQuery, { limit: 12 });
        const right = await http.search(glossQuery, { limit: 12 });

        expect(left.results.length).toBeGreaterThan(0);
        expect(right.results.map((item) => item.article.s)).toEqual(
          left.results.map((item) => item.article.s),
        );
        expect(right.results.map((item) => item.article.l)).toEqual(
          left.results.map((item) => item.article.l),
        );
        // Gloss-only: lemma/roman must not be the admission path for the hit.
        for (const item of right.results) {
          const lemma = normalizeAtlasText(item.article.l);
          const roman = item.article.r ? normalizeAtlasText(item.article.r) : "";
          const nq = normalizeAtlasText(glossQuery);
          expect(lemma === nq || lemma.startsWith(nq) || roman.startsWith(nq)).toBe(false);
          expect(normalizeAtlasText(item.article.g ?? "").includes(nq)).toBe(true);
        }
      } finally {
        if (movedIndex && existsSync(bakIndex)) renameSync(bakIndex, searchIndex);
        if (movedAliases && existsSync(bakAliases)) renameSync(bakAliases, searchAliases);
        if (prevAtlasDb === undefined) delete process.env.ATLAS_DB_PATH;
        else process.env.ATLAS_DB_PATH = prevAtlasDb;
        resetSqliteAtlasDataSourceCachesForTests();
        resetAtlasPayloadCacheForTests();
      }
    } finally {
      rmSync(outDir, { recursive: true, force: true });
    }
  });

  test("core module has no static node: imports (F004 source guard)", () => {
    const src = readFileSync(
      resolve(process.cwd(), "src/lib/lexicon/http-atlas-data-source.ts"),
      "utf-8",
    );
    expect(src).not.toMatch(/from\s+["']node:/);
    expect(src).not.toMatch(/require\(["']node:/);
  });
});
