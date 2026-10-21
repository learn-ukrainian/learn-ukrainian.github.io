import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { beforeAll, describe, expect, onTestFinished, test, vi } from "vitest";
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
import type { LexiconApiContract, LexiconRuntimeStatus } from "@site/src/lib/lexicon/runtime-contract";
import { buildCommittedLexiconRuntimeStatus as originalStatusMemo } from "@site/src/lib/lexicon/committed-runtime-status";

// Supplementary mechanics fixtures. The full-population inputs below remain
// owned by their original cold hook and static module bindings.
const MEMO_DAILY_INPUTS = {
  first: [{ id: 1 }],
  second: [{ id: 1 }, { id: 2 }, { id: 3 }],
  rebuilt: [{ id: 1 }, { id: 2 }],
};

function writeMemoFixture(root: string, dailyPool: { id: number }[]): void {
  const files: Record<string, unknown> = {
    "src/data/lexicon-manifest.json": {
      version: "memo-fixture-v1",
      generated_at: "2026-10-12T00:00:00Z",
      entries: [{
        lemma: "fixture",
        url_slug: "fixture",
        primary_source: "source_inventory_grow",
        surface_admission: { daily: true, practice: true, cloze: true },
      }],
    },
    "src/data/lexicon-manifest.pointer.json": {
      manifest_version: "memo-release-v1",
      generated_at: "2026-09-01T00:00:00Z",
      release_tag: "memo-artifact-v1",
      json_bytes: 1000,
      json_sha256: "synthetic-memo-artifact",
    },
    "src/data/lexicon-search-index.json": [{ t: "lemma" }],
    "src/data/lexicon-search-aliases.json": [],
    "src/data/lexicon-search-shards.json": {},
    "src/data/lexicon-browse-meta.json": { total: 1, letterCounts: { F: 1 } },
    "src/data/lexicon-daily-pool.json": dailyPool,
    "src/data/lexicon-practice-cloze-sources.json": [],
    "src/data/lexicon-practice-reviewed-sources.json": [],
    "public/lexicon/practice-index.A1.json": {
      deckVersion: "memo-deck-v1",
      counts: { lexemes: 1, cloze: 1 },
    },
  };
  for (const [relativePath, content] of Object.entries(files)) {
    const path = join(root, relativePath);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, JSON.stringify(content));
  }
}

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

// Hydrated CI carries the ~218 MB lexicon-manifest.json; building the committed
// runtime status parses all of it (#10472: ~3 s on a quiet host, 7-11 s on a
// starved 2-core runner). That one-time fixture cost is paid in beforeAll under
// its own budget so it never lands inside a 5 s per-test budget.
const FIXTURE_BUILD_TIMEOUT_MS = 60_000;

let sharedSearch: unknown[];
let sharedDaily: unknown[];

async function routePaths(getStaticPaths: () => ReturnType<typeof practiceApiStaticPaths>): Promise<string[]> {
  const paths = await getStaticPaths();
  return paths.map((path) => {
    if (!("params" in path)) throw new Error("expected static params");
    return String(path.params.level);
  });
}

describe("lexicon static API routes", () => {
  beforeAll(async () => {
    // Status first: it primes the committed runtime-status cache that the status
    // and contract routes (and the tests below) then read in milliseconds.
    const statusStarted = performance.now();
    console.log('[10183-phase] path=status phase=status state=started');
    try {
      await routeJson(getStatus);
    } finally {
      console.log(`[10183-phase] path=status phase=status state=settled ms=${(performance.now() - statusStarted).toFixed(3)}`);
    }
    const searchStarted = performance.now();
    console.log('[10183-phase] path=status phase=search state=started');
    try {
      sharedSearch = await routeJson<unknown[]>(getSearchIndex);
    } finally {
      console.log(`[10183-phase] path=status phase=search state=settled ms=${(performance.now() - searchStarted).toFixed(3)}`);
    }
    const dailyStarted = performance.now();
    console.log('[10183-phase] path=status phase=daily state=started');
    try {
      sharedDaily = await routeJson<unknown[]>(getDailyPool);
    } finally {
      console.log(`[10183-phase] path=status phase=daily state=settled ms=${(performance.now() - dailyStarted).toFixed(3)}`);
    }
  }, FIXTURE_BUILD_TIMEOUT_MS);

  test.each(["status", "contract"])(
    "isolates served status and contract memos with %s as first reader and explicit test reset",
    async (firstReader) => {
      // The original beforeAll has already paid the full cold-build cost.
      const originalMemo = originalStatusMemo();
      const originalStatus = await (await getStatus({} as Parameters<APIRoute>[0])).text();
      const originalContract = await (await getContract({} as Parameters<APIRoute>[0])).text();
      const scratch = mkdtempSync(join(tmpdir(), "lexicon-route-memo-"));
      let restoreCwd = () => {};
      let resetPrivateMemo = () => {};
      // Vitest reports teardown errors alongside a primary assertion failure.
      onTestFinished(async () => {
        restoreCwd();
        try {
          resetPrivateMemo();
          vi.resetModules();
        } finally {
          rmSync(scratch, { recursive: true, force: true });
        }
        expect(originalStatusMemo()).toBe(originalMemo);
        expect(await (await getStatus({} as Parameters<APIRoute>[0])).text()).toBe(originalStatus);
        expect(await (await getContract({} as Parameters<APIRoute>[0])).text()).toBe(originalContract);
      });

      const rootA = join(scratch, "a");
      const rootB = join(scratch, "b");
      writeMemoFixture(rootA, MEMO_DAILY_INPUTS.first);
      writeMemoFixture(rootB, MEMO_DAILY_INPUTS.second);
      vi.resetModules();
      const privateMemo = await import("@site/src/lib/lexicon/committed-runtime-status");
      resetPrivateMemo = privateMemo.resetCommittedLexiconRuntimeStatusForTests;
      expect(privateMemo.buildCommittedLexiconRuntimeStatus).not.toBe(originalStatusMemo);
      const { GET: privateStatus } = await import("@site/src/pages/api/lexicon/status.json");
      const { GET: privateContract } = await import("@site/src/pages/api/lexicon/contract.json");
      const cwdSpy = vi.spyOn(process, "cwd").mockReturnValue(rootA);
      restoreCwd = () => cwdSpy.mockRestore();

      async function observe(root: string, dailyCount: number): Promise<void> {
        cwdSpy.mockReturnValue(root);
        async function status(): Promise<void> {
          const response = await privateStatus({} as Parameters<APIRoute>[0]);
          expect(response.status).toBe(200);
          expect(response.headers.get("Content-Type")).toBe("application/json; charset=utf-8");
          expect(response.headers.get("Cache-Control")).toBe("public, max-age=3600");
          const payload: LexiconRuntimeStatus = await response.json();
          expect(payload.schema).toBe("atlas-runtime-status");
          expect(payload.status).toBe("ok");
          expect(payload.daily.poolEntries).toBe(dailyCount);
          expect(payload.manifest).toEqual({
            hydrated: true, records: 1, publicLexemeRecords: 1, grammarTermRecords: 0,
            version: "memo-fixture-v1", releaseTag: "memo-artifact-v1",
            generatedAt: "2026-10-12T00:00:00Z", jsonBytes: 1000,
            jsonSha256: "synthetic-memo-artifact",
          });
          expect(payload.sourceInventory).toEqual({
            atlasRows: 1, dailyAdmitted: 1, practiceAdmitted: 1, clozeAdmitted: 1,
          });
        }
        async function contract(): Promise<void> {
          const response = await privateContract({} as Parameters<APIRoute>[0]);
          expect(response.status).toBe(200);
          expect(response.headers.get("Content-Type")).toBe("application/json; charset=utf-8");
          expect(response.headers.get("Cache-Control")).toBe("public, max-age=3600");
          const payload: LexiconApiContract = await response.json();
          expect(payload.schema).toBe("atlas-api-contract");
          expect(payload.status).toBe("ok");
          expect(payload.staticOnly).toBe(true);
          expect(payload.surfaces.dailyWord).toEqual({
            poolEntries: dailyCount, endpoint: "/lexicon/daily-pool.json", admission: "reviewed-static-pool",
          });
          expect(payload.surfaces.atlas.totalReviewedEntries).toBe(1);
          expect(payload.surfaces.practice.deckVersions).toEqual(["memo-deck-v1"]);
        }
        if (firstReader === "status") {
          await status();
          await contract();
        } else {
          await contract();
          await status();
        }
      }

      await observe(rootA, 1);
      await observe(rootB, 3);
      await observe(rootA, 1);
      writeFileSync(join(rootA, "src/data/lexicon-daily-pool.json"), JSON.stringify(MEMO_DAILY_INPUTS.rebuilt));
      // Same-root file changes have no automatic invalidation promise.
      await observe(rootA, 1);
      resetPrivateMemo();
      await observe(rootA, 2);
      await observe(rootB, 3);
    },
  );

  test("emits runtime status for public Atlas, Daily Word, and Practice", async () => {
    const started = performance.now();
    console.log('[10183-phase] path=status phase=assert state=started');
    try {
      const search = sharedSearch;
      const daily = sharedDaily;
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
      expect(status.endpoints.searchIndex).toBe("/lexicon/search-index.json");
      expect(status.endpoints.searchAliases).toBe("/lexicon/search-aliases.json");
      expect(status.endpoints.searchShards).toBe("/lexicon/search-shards.json");
      expect(status.endpoints.dailyPool).toBe("/lexicon/daily-pool.json");
      expect(status.endpoints.practiceIndexTemplate).toBe(
        "/lexicon/practice-index.{level}.json",
      );
      expect(status.endpoints.practiceLexemesTemplate).toBe(
        "/lexicon/practice-lexemes.{level}.json",
      );
      expect(status.endpoints.practiceClozeTemplate).toBe(
        "/lexicon/practice-cloze.{level}.json",
      );
    } finally {
      console.log(`[10183-phase] path=status phase=assert state=settled ms=${(performance.now() - started).toFixed(3)}`);
    }
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
    // Hydrated practice deck after inventory-cloze scale (#6179/#6182): do not pin
    // an exact historical total; assert the published contract is non-trivial.
    expect(contract.surfaces.cloze.totalItems).toBeGreaterThanOrEqual(200);
    expect(contract.surfaces.cloze.reviewedSourceRows).toBeGreaterThan(0);
    expect(contract.endpoints.practiceIndexTemplate).toBe(
      "/lexicon/practice-index.{level}.json",
    );
  });

  test("publishes separate article and alias search artifacts under /lexicon (with /api aliases)", async () => {
    const search = sharedSearch;
    const aliases = await routeJson<Array<{ a: string; s: string; h: string }>>(getSearchAliases);
    const daily = sharedDaily;

    expect(search.length).toBeGreaterThan(5000);
    expect(aliases.length).toBeGreaterThan(5000);
    expect(aliases).toContainEqual(expect.objectContaining({ a: "Іване", s: "іван", h: "Іван" }));
    expect(daily.length).toBeGreaterThanOrEqual(250);
  });

  test("aliases static practice shards under /api/lexicon (hydrate copy of /lexicon)", async () => {
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
    // A1 cloze is inventory+curriculum sourced; exact count floats with deck
    // publish. Require index/cloze shard agreement (above) and a post-#6179 floor.
    expect(index.counts.cloze).toBeGreaterThanOrEqual(100);
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
