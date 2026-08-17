// @vitest-environment node
/**
 * GH #4385 remainder — prove publisher SSG consumes atlas.db and fails closed
 * when the catalog is missing/empty/wrong. Fixture DB only (no hydrate).
 */

import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, test } from "vitest";
import {
  atlasStaticRoutesEnabled,
  buildAtlasStaticPaths,
} from "@site/src/lib/lexicon/atlas-static-paths";
import {
  resetAtlasPayloadCacheForTests,
} from "@site/src/lib/lexicon/atlasDb";
import {
  resetSqliteAtlasDataSourceCachesForTests,
  SqliteAtlasDataSource,
} from "@site/src/lib/lexicon/sqlite-atlas-data-source";

const fixtureDb = resolve(process.cwd(), "../tests/fixtures/atlas/runtime_shards_fixture.db");
const hasFixture = existsSync(fixtureDb);
const packageJson = JSON.parse(
  readFileSync(resolve(process.cwd(), "package.json"), "utf8"),
) as { scripts: Record<string, string> };

function resetCaches(): void {
  resetAtlasPayloadCacheForTests();
  resetSqliteAtlasDataSourceCachesForTests();
}

describe("ATLAS_STATIC_ROUTES publisher SSG contract (#4385)", () => {
  afterEach(() => {
    delete process.env.ATLAS_DB_PATH;
    delete process.env.ATLAS_STATIC_ROUTES;
    resetCaches();
  });

  test("npm run build / build:full enable ATLAS_STATIC_ROUTES; build:shell does not", () => {
    expect(packageJson.scripts.build).toContain("ATLAS_STATIC_ROUTES=1");
    expect(packageJson.scripts["build:full"]).toContain("ATLAS_STATIC_ROUTES=1");
    expect(packageJson.scripts.build).toContain("hydrate");
    expect(packageJson.scripts["build:shell"]).not.toContain("ATLAS_STATIC_ROUTES");
    expect(atlasStaticRoutesEnabled({})).toBe(false);
    expect(atlasStaticRoutesEnabled({ ATLAS_STATIC_ROUTES: "1" })).toBe(true);
  });

  test("without ATLAS_STATIC_ROUTES, getStaticPaths returns [] (client-shell mode)", async () => {
    const paths = await buildAtlasStaticPaths({});
    expect(paths).toEqual([]);
  });

  test.skipIf(!hasFixture)(
    "ATLAS_STATIC_ROUTES=1 against fixture atlas.db emits catalog routes and fails if empty",
    async () => {
      process.env.ATLAS_DB_PATH = fixtureDb;
      resetCaches();

      const paths = await buildAtlasStaticPaths({ ATLAS_STATIC_ROUTES: "1" });
      expect(paths.length).toBeGreaterThan(0);

      const source = new SqliteAtlasDataSource();
      const catalog = source.getStaticCatalog();
      expect(paths.map((p) => p.params.lemma)).toEqual([...catalog.routeSlugs]);
      expect(paths.every((p) => p.props.record.entry.url_slug === p.params.lemma)).toBe(true);
      expect(paths[0]?.props.manifestVersion).toBe(catalog.manifestVersion);

      await expect(
        buildAtlasStaticPaths({ ATLAS_STATIC_ROUTES: "1" }, () => {
          return {
            getStaticCatalog: () => ({
              sourceVersion: "sqlite-empty",
              generatedAt: "1970-01-01T00:00:00Z",
              manifestVersion: "empty",
              routeSlugs: [],
            }),
            getEntry: async () => ({ kind: "missing" as const, version: "sqlite-empty", slug: "x" }),
          } as unknown as SqliteAtlasDataSource;
        }),
      ).rejects.toThrow(/Atlas static catalog is empty/);
    },
  );

  test("ATLAS_STATIC_ROUTES=1 fails closed when atlas.db is missing", async () => {
    process.env.ATLAS_DB_PATH = resolve(process.cwd(), "../data/atlas-missing-ssg-gate.db");
    resetCaches();
    await expect(buildAtlasStaticPaths({ ATLAS_STATIC_ROUTES: "1" })).rejects.toThrow(
      /Atlas DB not found/,
    );
  });
});
