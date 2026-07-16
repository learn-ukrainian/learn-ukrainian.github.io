// @vitest-environment node

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";
import { normalizeAtlasText } from "@site/src/lib/lexicon/normalize";
import {
  createFileAtlasFetch,
  HttpAtlasDataSource,
} from "@site/src/lib/lexicon/http-atlas-data-source";
import {
  COMPONENT_TOKEN_RE,
  resetSqliteAtlasDataSourceCachesForTests,
  SqliteAtlasDataSource,
} from "@site/src/lib/lexicon/sqlite-atlas-data-source";
import { AtlasDataSourceError } from "@site/src/lib/lexicon/atlas-data-source";
import { rankSearchResults } from "@site/src/lib/lexicon/search";
import reactRenderer from "@astrojs/react/server.js";
import { experimental_AstroContainer as AstroContainer } from "astro/container";
import {
  getAtlasPayloadCache,
  resetAtlasPayloadCacheForTests,
} from "@site/src/lib/lexicon/atlasDb";

const vectorsPath = resolve(
  process.cwd(),
  "../scripts/atlas/normalization_vectors.json",
);
const exportRoot = resolve(process.cwd(), "../build/atlas-runtime");
const atlasDbPath = resolve(process.cwd(), "../data/atlas.db");
const hasAtlasDb = existsSync(atlasDbPath);
const hasExportRoot = existsSync(resolve(exportRoot, "atlas/current.json"));

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
      const http = new HttpAtlasDataSource(createFileAtlasFetch(exportRoot));

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
      const http = new HttpAtlasDataSource(createFileAtlasFetch(exportRoot));
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
      const http = new HttpAtlasDataSource(createFileAtlasFetch(exportRoot));
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
    const http = new HttpAtlasDataSource(createFileAtlasFetch(exportRoot));
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
    const http = new HttpAtlasDataSource(createFileAtlasFetch(exportRoot));
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
    const httpProbe = new HttpAtlasDataSource(createFileAtlasFetch(exportRoot));
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
    const { writeFileSync } = await import("node:fs");
    writeFileSync(shardPath, corrupted);
    const http = new HttpAtlasDataSource(createFileAtlasFetch(exportRoot));
    try {
      await expect(http.getEntry("прапор")).rejects.toBeInstanceOf(AtlasDataSourceError);
    } finally {
      writeFileSync(shardPath, original);
    }
  });
});
