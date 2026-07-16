// @vitest-environment node

import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";
import {
  ATLAS_ENTRY_TYPES,
  getAtlasPayloadCache,
  getPracticeLemmas,
  resetAtlasPayloadCacheForTests,
} from "@site/src/lib/lexicon/atlasDb";
import {
  resetSqliteAtlasDataSourceCachesForTests,
  SqliteAtlasDataSource,
} from "@site/src/lib/lexicon/sqlite-atlas-data-source";

const fixtureDb = resolve(process.cwd(), "../tests/fixtures/atlas/runtime_shards_fixture.db");
const productionDb = resolve(process.cwd(), "../data/atlas.db");
const hasFixture = existsSync(fixtureDb);
const hasProduction = existsSync(productionDb);

const REQUIRED_TYPES = [...ATLAS_ENTRY_TYPES, "form_route"] as const;

describe("SqliteAtlasDataSource static catalog + practice reconciliation", () => {
  test.skipIf(!hasFixture)("fixture DB covers every ATLAS_ENTRY_TYPES value plus form_route", () => {
    const previous = process.env.ATLAS_DB_PATH;
    process.env.ATLAS_DB_PATH = fixtureDb;
    try {
      resetAtlasPayloadCacheForTests();
      resetSqliteAtlasDataSourceCachesForTests();
      const source = new SqliteAtlasDataSource();
      const catalog = source.getStaticCatalog();
      const present = new Set<string>();
      const cache = getAtlasPayloadCache();
      for (const entry of cache.entries) {
        present.add(entry.entry_type ?? "form_route");
      }
      expect([...present].sort()).toEqual([...REQUIRED_TYPES].sort());
      expect(catalog.routeSlugs).toEqual(cache.entries.map((entry) => entry.url_slug));
      expect(catalog.manifestVersion).toBe(cache.manifestVersion);
      expect(catalog.generatedAt).toBe(cache.generatedAt);
      expect(catalog.sourceVersion).toBe(`sqlite-${cache.manifestVersion}`);
      expect(catalog.routeSlugs).not.toContain("fixture-missing-sentinel");
      process.stdout.write(
        `fixture type-set coverage: ${REQUIRED_TYPES.join(" ")} (exact)\n`,
      );
    } finally {
      if (previous === undefined) delete process.env.ATLAS_DB_PATH;
      else process.env.ATLAS_DB_PATH = previous;
      resetAtlasPayloadCacheForTests();
      resetSqliteAtlasDataSourceCachesForTests();
    }
  });

  test.skipIf(!hasProduction)(
    "practiceLevels length mirrors legacy getPracticeLemmas visibility",
    async () => {
      resetAtlasPayloadCacheForTests();
      resetSqliteAtlasDataSourceCachesForTests();
      const legacy = getPracticeLemmas();
      const source = new SqliteAtlasDataSource();
      const catalog = source.getStaticCatalog();

      let checked = 0;
      for (const slug of catalog.routeSlugs.slice(0, 200)) {
        const result = await source.getEntry(slug, {
          expectedVersion: catalog.sourceVersion,
        });
        expect(result.kind).toBe("entry");
        if (result.kind !== "entry") continue;
        const legacyHas =
          legacy.has(result.record.entry.url_slug) || legacy.has(result.record.entry.lemma);
        const nextHas = result.record.renderContext.practiceLevels.length > 0;
        expect(nextHas, slug).toBe(legacyHas);
        checked += 1;
      }
      expect(checked).toBeGreaterThan(0);
    },
  );

  test.skipIf(!hasProduction)(
    "componentLinks on EntryRecord match legacy chip href targets for multiword fixtures",
    async () => {
      resetAtlasPayloadCacheForTests();
      resetSqliteAtlasDataSourceCachesForTests();
      const cache = getAtlasPayloadCache();
      const source = new SqliteAtlasDataSource();
      for (const slug of ["будь-ласка", "доконаний-вид"]) {
        const result = await source.getEntry(slug);
        expect(result.kind).toBe("entry");
        if (result.kind !== "entry") continue;
        const entry = cache.bySlug.get(slug)!;
        const tokens = entry.lemma.match(/[\p{L}\p{M}]+(?:['’][\p{L}\p{M}]+)*/gu) ?? [];
        expect(result.record.renderContext.componentLinks.map((link) => link.text)).toEqual(
          tokens,
        );
        for (const link of result.record.renderContext.componentLinks) {
          if (!link.targetSlug) continue;
          expect(cache.bySlug.get(link.targetSlug)?.entry_type).toBe("lemma");
        }
      }
    },
  );
});
