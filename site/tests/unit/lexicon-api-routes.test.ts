import { describe, expect, test } from "vitest";
import type { APIRoute, GetStaticPaths } from "astro";
import { GET as getDailyPool } from "@site/src/pages/api/lexicon/daily-pool.json";
import {
  GET as getPracticeCloze,
  getStaticPaths as getPracticeClozePaths,
} from "@site/src/pages/api/lexicon/practice-cloze.[level].json";
import {
  GET as getPracticeIndex,
  getStaticPaths as getPracticeIndexPaths,
} from "@site/src/pages/api/lexicon/practice-index.[level].json";
import {
  GET as getPracticeLexemes,
  getStaticPaths as getPracticeLexemesPaths,
} from "@site/src/pages/api/lexicon/practice-lexemes.[level].json";
import { GET as getSearchIndex } from "@site/src/pages/api/lexicon/search-index.json";
import { GET as getStatus } from "@site/src/pages/api/lexicon/status.json";
import { PRACTICE_LEVELS } from "@site/src/lib/lexicon/runtime-contract";

async function routeJson<T>(
  route: APIRoute,
  params: Record<string, string | undefined> = {},
): Promise<T> {
  const response = await route({ params } as Parameters<APIRoute>[0]);
  expect(response).toBeInstanceOf(Response);
  expect(response.headers.get("Content-Type")).toContain("application/json");
  return (await response.json()) as T;
}

async function routePaths(getStaticPaths: GetStaticPaths): Promise<string[]> {
  const paths = await getStaticPaths({ paginate: () => [] } as Parameters<GetStaticPaths>[0]);
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
      publicAtlas: { searchEntries: number; browseEntries: number };
      daily: { poolEntries: number };
      practice: { totalLexemes: number };
      checks: { searchMatchesBrowse: boolean; singlePracticeDeckVersion: boolean };
      endpoints: {
        searchIndex: string;
        dailyPool: string;
        practiceIndexTemplate: string;
        practiceLexemesTemplate: string;
        practiceClozeTemplate: string;
      };
    }>(getStatus);

    expect(status.schema).toBe("atlas-runtime-status");
    expect(status.status).toBe("ok");
    expect(status.publicAtlas.searchEntries).toBe(search.length);
    expect(status.publicAtlas.searchEntries).toBe(status.publicAtlas.browseEntries);
    expect(status.daily.poolEntries).toBe(daily.length);
    expect(status.practice.totalLexemes).toBeGreaterThan(0);
    expect(status.checks.searchMatchesBrowse).toBe(true);
    expect(status.checks.singlePracticeDeckVersion).toBe(true);
    expect(status.endpoints.searchIndex).toBe("/api/lexicon/search-index.json");
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

  test("aliases search and Daily Word data under /api/lexicon", async () => {
    const search = await routeJson<unknown[]>(getSearchIndex);
    const daily = await routeJson<unknown[]>(getDailyPool);

    expect(search.length).toBeGreaterThan(5000);
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
  expect(index.counts.cloze).toBe(14);
});
});
