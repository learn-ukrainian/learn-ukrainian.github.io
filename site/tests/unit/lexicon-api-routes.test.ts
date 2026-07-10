import { describe, expect, test } from "vitest";
import type { APIRoute } from "astro";
import { GET as getContract } from "@site/src/pages/api/lexicon/contract.json";
import { GET as getDailyPool } from "@site/src/pages/api/lexicon/daily-pool.json";
import {
  practiceApiStaticPaths,
  practiceShardResponse,
} from "@site/src/lib/lexicon/practice-api-shard";
import {
  searchApiStaticPaths,
  searchShardResponse,
} from "@site/src/lib/lexicon/search-api-shard";
import { GET as getSearchIndex } from "@site/src/pages/api/lexicon/search-index.json";
import { GET as getSearchAliases } from "@site/src/pages/lexicon/search-aliases.json";
import { GET as getStatus } from "@site/src/pages/api/lexicon/status.json";
import { PRACTICE_LEVELS } from "@site/src/lib/lexicon/runtime-contract";

const getPracticeCloze: APIRoute = ({ params }) =>
  practiceShardResponse("practice-cloze", params.level);
const getPracticeIndex: APIRoute = ({ params }) =>
  practiceShardResponse("practice-index", params.level);
const getPracticeLexemes: APIRoute = ({ params }) =>
  practiceShardResponse("practice-lexemes", params.level);
const getPracticeClozePaths = practiceApiStaticPaths;
const getPracticeIndexPaths = practiceApiStaticPaths;
const getPracticeLexemesPaths = practiceApiStaticPaths;

async function routeJson<T>(
  route: APIRoute,
  params: Record<string, string | undefined> = {},
): Promise<T> {
  const response = await route({ params } as Parameters<APIRoute>[0]);
  expect(response).toBeInstanceOf(Response);
  expect(response.headers.get("Content-Type")).toContain("application/json");
  return (await response.json()) as T;
}

async function routePaths(getStaticPaths: () => ReturnType<typeof practiceApiStaticPaths>): Promise<string[]> {
  const paths = await getStaticPaths();
  return paths.map((path) => {
    if (!("params" in path)) throw new Error("expected static params");
    return String(path.params.level);
  });
}

describe("lexicon static API routes", () => {
  test("emits runtime status for public Atlas, Daily Word, and Practice", async () => {
    const search = await routeJson<unknown[]>(getSearchIndex);
    const daily = await routeJson<unknown[]>(getDailyPool);
    const status = await routeJson<{
      schema: string;
      status: string;
      publicAtlas: { searchArticleEntries: number; searchAliasRows: number; browseRecords: number };
      entryModel: {
        reviewed_entries_by_type: Record<string, number>;
        total_reviewed_entries: number;
        alias_records: number;
        candidate_evidence_count: number;
        candidate_evidence_by_bucket: Record<string, number>;
      };
      daily: { poolEntries: number };
      practice: { totalLexemes: number };
      checks: { searchMatchesReviewedEntries: boolean; singlePracticeDeckVersion: boolean };
      endpoints: {
        contract: string;
        searchIndex: string;
        searchAliases: string;
        searchShards: string;
      dailyPool: string;
      practiceIndexTemplate: string;
        practiceLexemesTemplate: string;
        practiceClozeTemplate: string;
      };
    }>(getStatus);

    expect(status.schema).toBe("atlas-runtime-status");
    expect(status.status).toBe("ok");
    expect(status.publicAtlas.searchArticleEntries).toBe(search.length);
    expect(status.publicAtlas.searchArticleEntries).toBe(status.entryModel.total_reviewed_entries);
    expect(Object.values(status.entryModel.reviewed_entries_by_type).reduce((sum, count) => sum + count, 0)).toBe(
      status.entryModel.total_reviewed_entries,
    );
    expect(status.publicAtlas.searchAliasRows).toBeGreaterThan(0);
    expect(status.entryModel.alias_records).toBeGreaterThanOrEqual(status.publicAtlas.searchAliasRows);
    expect(status.entryModel.candidate_evidence_count).toBe(0);
    expect(status.entryModel.candidate_evidence_by_bucket).toEqual({});
    expect(status.daily.poolEntries).toBe(daily.length);
    expect(status.practice.totalLexemes).toBeGreaterThan(0);
    expect(status.checks.searchMatchesReviewedEntries).toBe(true);
    expect(status.checks.singlePracticeDeckVersion).toBe(true);
    expect(status.endpoints.contract).toBe("/api/lexicon/contract.json");
    expect(status.endpoints.searchIndex).toBe("/api/lexicon/search-index.json");
    expect(status.endpoints.searchAliases).toBe("/lexicon/search-aliases.json");
  expect(status.endpoints.searchShards).toBe("/lexicon/search-shards.json");
  expect(status.endpoints.dailyPool).toBe("/api/lexicon/daily-pool.json");
    expect(status.endpoints.practiceIndexTemplate).toBe(
      "/api/lexicon/practice-index.{level}.json",
    );
    expect(status.endpoints.practiceLexemesTemplate).toBe(
      "/api/lexicon/practice-lexemes.{level}.json",
    );
    expect(status.endpoints.practiceClozeTemplate).toBe(
      "/api/lexicon/practice-cloze.{level}.json",
    );
  });

  test("publishes one static API contract for Atlas, Daily Word, and practice", async () => {
    const contract = await routeJson<{
      schema: string;
      staticOnly: boolean;
      surfaces: {
        atlas: {
          totalReviewedEntries: number;
          reviewedEntriesByType: Record<string, number>;
          aliasRecords: number;
          candidateEvidenceCount: number;
          searchShards: number;
          browseRecords: number;
        };
        dailyWord: { poolEntries: number; endpoint: string };
        practice: { totalLexemes: number; levels: string[] };
        cloze: { totalItems: number; reviewedSourceRows: number };
      };
      endpoints: { contract: string; dailyPool: string; practiceIndexTemplate: string };
    }>(getContract);

    expect(contract.schema).toBe("atlas-api-contract");
    expect(contract.staticOnly).toBe(true);
    expect(contract.endpoints.contract).toBe("/api/lexicon/contract.json");
    expect(contract.surfaces.atlas.totalReviewedEntries).toBeGreaterThan(5000);
    expect(contract.surfaces.atlas.reviewedEntriesByType.lemma).toBeGreaterThan(4000);
    expect(contract.surfaces.atlas.aliasRecords).toBeGreaterThan(5000);
    expect(contract.surfaces.atlas.candidateEvidenceCount).toBe(0);
    expect(contract.surfaces.atlas.browseRecords).toBeGreaterThanOrEqual(
      contract.surfaces.atlas.totalReviewedEntries,
    );
    expect(contract.surfaces.atlas.searchShards).toBeGreaterThan(1);
    expect(contract.surfaces.dailyWord.poolEntries).toBeGreaterThanOrEqual(250);
    expect(contract.surfaces.dailyWord.endpoint).toBe(contract.endpoints.dailyPool);
    expect(contract.surfaces.practice.totalLexemes).toBeGreaterThan(1000);
    expect(contract.surfaces.practice.levels).toEqual([...PRACTICE_LEVELS]);
    expect(contract.surfaces.cloze.totalItems).toBe(22);
    expect(contract.surfaces.cloze.reviewedSourceRows).toBeGreaterThan(0);
    expect(contract.endpoints.practiceIndexTemplate).toBe(
      "/api/lexicon/practice-index.{level}.json",
    );
  });

  test("publishes separate article and alias search artifacts under /api/lexicon", async () => {
    const search = await routeJson<unknown[]>(getSearchIndex);
    const aliases = await routeJson<Array<{ a: string; s: string; h: string }>>(getSearchAliases);
    const daily = await routeJson<unknown[]>(getDailyPool);

    expect(search.length).toBeGreaterThan(5000);
    expect(aliases.length).toBeGreaterThan(5000);
    expect(aliases).toContainEqual(expect.objectContaining({ a: "Іване", s: "іван", h: "Іван" }));
    expect(daily.length).toBeGreaterThanOrEqual(250);
  });

  test("aliases static practice shards under /api/lexicon", async () => {
    await expect(routePaths(getPracticeIndexPaths)).resolves.toEqual([...PRACTICE_LEVELS]);
    await expect(routePaths(getPracticeLexemesPaths)).resolves.toEqual([...PRACTICE_LEVELS]);
    await expect(routePaths(getPracticeClozePaths)).resolves.toEqual([...PRACTICE_LEVELS]);

    const index = await routeJson<{
      level: string;
      deckVersion: string;
      counts: { lexemes: number; cloze: number };
    }>(getPracticeIndex, { level: "A1" });
    const lexemes = await routeJson<{
      level: string;
      deckVersion: string;
      lexemes: unknown[];
    }>(getPracticeLexemes, { level: "A1" });
    const cloze = await routeJson<{
      level: string;
      deckVersion: string;
      cloze: unknown[];
    }>(getPracticeCloze, { level: "A1" });

    expect(index.level).toBe("A1");
    expect(lexemes.level).toBe("A1");
    expect(cloze.level).toBe("A1");
    expect(index.deckVersion).toBe(lexemes.deckVersion);
    expect(index.deckVersion).toBe(cloze.deckVersion);
    expect(index.counts.lexemes).toBe(lexemes.lexemes.length);
  expect(index.counts.cloze).toBe(cloze.cloze.length);
  expect(index.counts.lexemes).toBeGreaterThan(1000);
    expect(index.counts.cloze).toBe(22);
  });

  test("materializes search shards for static /lexicon/search/{shard}.json URLs", async () => {
    const paths = searchApiStaticPaths();
    expect(paths.length).toBeGreaterThan(1);

    const response = searchShardResponse("u043e");
    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toContain("application/json");
    expect(response.headers.get("Cache-Control")).toBe("public, max-age=3600");
    const rows = (await response.json()) as unknown[];
    expect(rows.length).toBeGreaterThan(0);
  });
});
