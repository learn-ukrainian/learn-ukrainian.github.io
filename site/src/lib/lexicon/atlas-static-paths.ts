/**
 * Publisher SSG path enumeration for `/lexicon/[lemma]` (GH #4385).
 *
 * Pages uses `ATLAS_STATIC_ROUTES=a1` for the published A1 lemma allow-list.
 * Other word routes fall through to the client shell on 404. `build:full`
 * (`ATLAS_STATIC_ROUTES=1`) remains the full SQLite diagnostic build.
 */

import inventory from "../../../../registry/atlas/a1-v1-inventory.json";
import { PINNED_SELECTION_ENV, readRuntimeTreeIdentity } from "./atlas-artifact-selection.mjs";
import type { AtlasDataSource, EntryRecord } from "./atlas-data-source.ts";
import { atlasLinkCatalog } from "./atlas-link-catalog";
import { createFileAtlasFetch, createNodeHttpAtlasDataSource } from "./http-atlas-node.ts";
import { normalizeAtlasText } from "./normalize.ts";
import { SqliteAtlasDataSource, type AtlasStaticCatalog } from "./sqlite-atlas-data-source.ts";
import { buildAtlasLinkResolver, type Enrichment } from "./word-atlas-article-model";

const A1_STATIC_ROUTE_COUNT = 751;

export type AtlasStaticPath = {
  params: { lemma: string };
  props: { record: EntryRecord; generatedAt: string; manifestVersion: string };
};

export function atlasStaticRoutesEnabled(
  env: NodeJS.ProcessEnv = process.env,
): boolean {
  return env.ATLAS_STATIC_ROUTES === "1" || env.ATLAS_STATIC_ROUTES === "a1";
}

function a1RouteSlugs(): string[] {
  const evidence: Partial<Record<string, {
    inspect_word: { clean_analyses: readonly { entry_id: number; lemma: string }[] };
  }>> = inventory.word_evidence;
  const headwordKey = (word: string) => normalizeAtlasText(word).replace(/[’ʼ]/gu, "'");
  const headwords = new Set<string>();
  for (const { key, mapping } of inventory.rows) {
    if (mapping.kind === "lemma" && mapping.resolution === "resolved" && mapping.lemma) {
      headwords.add(headwordKey(mapping.lemma));
    } else if (mapping.kind === "ambiguous" && typeof mapping.evidence === "string") {
      // A spelling hub can serve an ambiguous row when the row itself is an
      // attested headword. An ambiguous inflection must not select a new lemma.
      const headword = headwordKey(key);
      const analyses = evidence[mapping.evidence]?.inspect_word.clean_analyses;
      if (analyses?.some(({ entry_id, lemma }) =>
        mapping.candidates.includes(entry_id) && headwordKey(lemma) === headword,
      )) {
        headwords.add(headword);
      }
    }
  }

  // The public catalog supplies canonical slugs, including apostrophe variants.
  // бариста is attested in the inventory and has no public Atlas route.
  const slugs = atlasLinkCatalog.entries
    .filter(({ entry_type, lemma }) => entry_type === "lemma" && headwords.has(headwordKey(lemma)))
    .map(({ slug }) => slug);
  const distinct = new Set(slugs).size;
  if (slugs.length !== A1_STATIC_ROUTE_COUNT || distinct !== A1_STATIC_ROUTE_COUNT) {
    throw new Error(
      `Expected ${A1_STATIC_ROUTE_COUNT} distinct A1 Atlas routes; found ${distinct} in ${slugs.length} catalog rows.`,
    );
  }
  return slugs;
}

export async function buildAtlasStaticPaths(
  env: NodeJS.ProcessEnv = process.env,
  sourceFactory: () => SqliteAtlasDataSource = () => new SqliteAtlasDataSource(),
): Promise<AtlasStaticPath[]> {
  if (!atlasStaticRoutesEnabled(env)) return [];

  if (env.ATLAS_STATIC_ROUTES === "a1") {
    const tree = env[PINNED_SELECTION_ENV]?.trim();
    if (!tree) throw new Error(`ATLAS_STATIC_ROUTES=a1 requires ${PINNED_SELECTION_ENV}`);
    const { dataVersion } = readRuntimeTreeIdentity(tree);
    const source = createNodeHttpAtlasDataSource(createFileAtlasFetch(tree), { assetBaseUrl: "" });
    return buildPaths(source, {
      sourceVersion: dataVersion,
      manifestVersion: dataVersion,
      generatedAt: dataVersion, // Matches the current client shell's displayed version.
      routeSlugs: a1RouteSlugs(),
    });
  }

  const source = sourceFactory();
  return buildPaths(source, source.getStaticCatalog());
}

async function buildPaths(
  source: Pick<AtlasDataSource, "getEntry">,
  catalog: AtlasStaticCatalog,
): Promise<AtlasStaticPath[]> {
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
    let record = result.record;
    const enrichment = record.entry.enrichment as Enrichment | null | undefined;
    const partnerHint = enrichment?.verb_pedagogy?.aspect_partner?.url_slug;
    const rawPartnerSlug = typeof partnerHint === "string" ? partnerHint.trim() : "";
    if (!record.partnerRecord && rawPartnerSlug) {
      const resolver = buildAtlasLinkResolver(
        atlasLinkCatalog,
        record.relations.map((relation) => relation.related_slug),
      );
      const partnerSlug = resolver.resolveSlug(rawPartnerSlug, slug);
      if (partnerSlug) {
        try {
          const partner = await source.getEntry(partnerSlug, { expectedVersion: catalog.sourceVersion });
          if (partner.kind === "entry") record = { ...record, partnerRecord: partner.record };
        } catch {
          // The partner is optional, as in the client shell.
        }
      }
    }
    paths.push({
      params: { lemma: slug },
      props: {
        record,
        generatedAt: catalog.generatedAt,
        manifestVersion: catalog.manifestVersion,
      },
    });
  }
  return paths;
}
