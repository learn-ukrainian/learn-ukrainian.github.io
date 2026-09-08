/**
 * Publisher SSG path enumeration for `/lexicon/[lemma]` (GH #4385).
 *
 * Production `npm run build` leaves `ATLAS_STATIC_ROUTES` unset so the site
 * builds in client-shell mode, avoiding thousands of prerendered HTML pages and
 * serving word detail dynamically via WordAtlasClientShell on 404.
 * Full diagnostic SSG remains available via `npm run build:full` (`ATLAS_STATIC_ROUTES=1`).
 */

import { SqliteAtlasDataSource } from "./sqlite-atlas-data-source.ts";
import type { EntryRecord } from "./atlas-data-source.ts";

export type AtlasStaticPath = {
  params: { lemma: string };
  props: { record: EntryRecord; generatedAt: string; manifestVersion: string };
};

export function atlasStaticRoutesEnabled(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return env.ATLAS_STATIC_ROUTES === "1";
}

/**
 * Enumerate lexicon article static paths from the Atlas SQLite catalog.
 *
 * - Env unset → `[]` (client-shell build; intentional).
 * - Env `=1` → fail closed if the DB/catalog is missing, empty, or a catalog
 *   slug cannot be loaded under the pinned source version.
 */
export async function buildAtlasStaticPaths(
  env: NodeJS.ProcessEnv = process.env,
  sourceFactory: () => SqliteAtlasDataSource = () => new SqliteAtlasDataSource(),
): Promise<AtlasStaticPath[]> {
  if (!atlasStaticRoutesEnabled(env)) return [];

  const source = sourceFactory();
  const catalog = source.getStaticCatalog();
  if (catalog.routeSlugs.length === 0) {
    throw new Error(
      "Atlas static catalog is empty under ATLAS_STATIC_ROUTES=1; " +
        "hydrate data/atlas.db (npm run hydrate / atlas:build-db) before building.",
    );
  }

  const paths: AtlasStaticPath[] = [];
  for (const slug of catalog.routeSlugs) {
    const result = await source.getEntry(slug, {
      expectedVersion: catalog.sourceVersion,
    });
    if (result.kind === "missing") {
      throw new Error(
        `Atlas static catalog slug missing under pinned version ${catalog.sourceVersion}: ${JSON.stringify(slug)}`,
      );
    }
    paths.push({
      params: { lemma: slug },
      props: {
        record: result.record,
        generatedAt: catalog.generatedAt,
        manifestVersion: catalog.manifestVersion,
      },
    });
  }
  return paths;
}
