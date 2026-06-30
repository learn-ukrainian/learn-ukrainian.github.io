import { describe, expect, test } from "vitest";
import { GET as getDailyPool } from "@site/src/pages/api/lexicon/daily-pool.json";
import { GET as getSearchIndex } from "@site/src/pages/api/lexicon/search-index.json";
import { GET as getStatus } from "@site/src/pages/api/lexicon/status.json";

async function routeJson<T>(route: typeof getStatus): Promise<T> {
  const response = await route({} as Parameters<typeof route>[0]);
  expect(response).toBeInstanceOf(Response);
  expect(response.headers.get("Content-Type")).toContain("application/json");
  return (await response.json()) as T;
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
      endpoints: { searchIndex: string; dailyPool: string };
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
  });

  test("aliases search and Daily Word data under /api/lexicon", async () => {
    const search = await routeJson<unknown[]>(getSearchIndex);
    const daily = await routeJson<unknown[]>(getDailyPool);

    expect(search.length).toBeGreaterThan(5000);
    expect(daily.length).toBeGreaterThanOrEqual(250);
  });
});
