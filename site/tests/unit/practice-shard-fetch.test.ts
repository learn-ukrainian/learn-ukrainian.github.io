import { afterEach, describe, expect, test, vi } from "vitest";
import {
  appendDrillFields,
  concatDrillFields,
  fetchPracticeDrillFields,
  getShardJson,
  isMissingShard,
  practiceDrillShardUrls,
  softSkipUnpublishedDrillShard,
  type PracticeDrillFields,
} from "@site/src/lib/lexicon/practice-shard-fetch";
import type { PracticeDeckData } from "@site/src/lib/lexicon/srs";

function jsonResponse(status: number, body: unknown = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const emptyFields: PracticeDrillFields = {
  cloze: [],
  stress: [],
  classify: [],
  paradigm: [],
  synonym: [],
  paronym: [],
  heritage: [],
  antonym: [],
};

describe("practice-shard-fetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  test("getShardJson tags HTTP status and evicts a failed URL from the cache", async () => {
    const cache = new Map<string, Promise<unknown>>();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(500))
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getShardJson("/lexicon/practice-synonym.A1.json", cache)).rejects.toMatchObject({
      status: 500,
    });
    expect(cache.size).toBe(0);

    await expect(getShardJson("/lexicon/practice-synonym.A1.json", cache)).resolves.toEqual({
      ok: true,
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  test("getShardJson shares one in-flight promise for the same URL", async () => {
    let resolveResponse: ((value: Response) => void) | undefined;
    const fetchMock = vi.fn(
      () =>
        new Promise<Response>((resolve) => {
          resolveResponse = resolve;
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const cache = new Map<string, Promise<unknown>>();

    const first = getShardJson("/lexicon/practice-index.A1.json", cache);
    const second = getShardJson("/lexicon/practice-index.A1.json", cache);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    resolveResponse!(jsonResponse(200, { items: [] }));
    await expect(Promise.all([first, second])).resolves.toEqual([{ items: [] }, { items: [] }]);
  });

  test("soft-skip unpublished drills (404) and rethrow other faults (#6768)", () => {
    const missing = Object.assign(new Error("missing"), { status: 404 });
    const server = Object.assign(new Error("server"), { status: 500 });
    expect(isMissingShard(missing)).toBe(true);
    expect(isMissingShard(server)).toBe(false);
    expect(softSkipUnpublishedDrillShard(missing)).toEqual({});
    expect(() => softSkipUnpublishedDrillShard(server)).toThrow(server);
    expect(() => softSkipUnpublishedDrillShard(new TypeError("Failed to fetch"))).toThrow(
      TypeError,
    );
  });

  test("practiceDrillShardUrls keeps the published kind order under /lexicon", () => {
    expect(practiceDrillShardUrls("/lexicon", "A1")).toEqual([
      "/lexicon/practice-cloze.A1.json",
      "/lexicon/practice-stress.A1.json",
      "/lexicon/practice-classify.A1.json",
      "/lexicon/practice-paradigm.A1.json",
      "/lexicon/practice-synonym.A1.json",
      "/lexicon/practice-paronym.A1.json",
      "/lexicon/practice-heritage.A1.json",
      "/lexicon/practice-antonym.A1.json",
    ]);
  });

  test("fetchPracticeDrillFields soft-skips 404 kinds and surfaces 5xx (#6768)", async () => {
    vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("practice-cloze.A1.json")) {
        return jsonResponse(200, { cloze: [{ clozeId: "c1" }] });
      }
      if (url.includes("practice-synonym.A1.json")) return jsonResponse(500);
      return jsonResponse(404);
    });

    await expect(fetchPracticeDrillFields("/lexicon", "A1", new Map())).rejects.toMatchObject({
      status: 500,
    });

    vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("practice-cloze.A1.json")) {
        return jsonResponse(200, { cloze: [{ clozeId: "c1" }] });
      }
      return jsonResponse(404);
    });

    await expect(fetchPracticeDrillFields("/lexicon", "A1", new Map())).resolves.toEqual({
      ...emptyFields,
      cloze: [{ clozeId: "c1" }],
    });
  });

  test("appendDrillFields concatenates selected-level then background batches", () => {
    const cloze = (clozeId: string) => ({ clozeId }) as PracticeDrillFields["cloze"][number];
    const deck = {
      deckVersion: "v1",
      level: "A1",
      index: [],
      lexemes: [],
      cloze: [cloze("core")],
    } as PracticeDeckData;
    const merged = appendDrillFields(
      deck,
      concatDrillFields([
        { ...emptyFields, cloze: [cloze("a1")] },
        { ...emptyFields, cloze: [cloze("a2")] },
      ]),
    );
    expect(merged.cloze.map((item) => item.clozeId)).toEqual(["core", "a1", "a2"]);
  });
});
