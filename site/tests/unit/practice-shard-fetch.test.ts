import { selectionReport, teacherReport } from '@site/src/lib/lexicon/practice-report-selection';
import { buildTeacherDeck } from '@site/src/lib/lexicon/teacher-deck';
import { bindDailyReport, dailyReportRecords } from '@site/src/lib/lexicon/practice-report-daily';
import type { DailyWord } from '@site/src/lib/lexicon/daily';
import type { DailyPracticeDeckItem, PracticeSelection, PracticeLexeme, PracticeIndexItem } from '@site/src/lib/lexicon/srs';
import { readFileSync } from 'node:fs';
import { createHash, webcrypto } from 'node:crypto';
import { parsePublicPracticeJson, practiceReportUrl, REPORT_DESTINATION } from '@site/src/lib/lexicon/practice-report';
import { afterEach, describe, expect, test, vi } from "vitest";
import {
  appendDrillFields,
  concatDrillFields,
  drillFieldsFromShardResults,
  fetchPracticeDrillFields,
  getShardJson,
  isMissingShard,
  isPracticeShardPublished,
  practiceDrillShardUrls,
  PUBLISHED_PRACTICE_SHARDS,
  setPublishedPracticeShardsForTesting,
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
  imperative: [],
};

describe("practice-shard-fetch", () => {
  afterEach(() => {
    setPublishedPracticeShardsForTesting(null);
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
    const urls = practiceDrillShardUrls("/lexicon", "A1");
    expect(urls).toHaveLength(7);
    expect(urls).toEqual([
      "/lexicon/practice-cloze.A1.json",
      "/lexicon/practice-stress.A1.json",
      "/lexicon/practice-classify.A1.json",
      "/lexicon/practice-paradigm.A1.json",
      "/lexicon/practice-paronym.A1.json",
      "/lexicon/practice-heritage.A1.json",
      "/lexicon/practice-imperative.A1.json",
    ]);
  });

  test("drill results map by kind when the synonym URL is skipped (#8714)", () => {
    const results = {
      imperative: { imperative: [{ imperativeId: "imperative-1" }] },
      paronym: { paronym: [{ paronymId: "paronym-1" }] },
      synonym: { synonym: [{ synonymId: "withdrawn" }] },
      cloze: { cloze: [{ clozeId: "cloze-1" }] },
    };
    const fields = drillFieldsFromShardResults(results);
    expect(fields.cloze).toEqual([{ clozeId: "cloze-1" }]);
    expect(fields.paronym).toEqual([{ paronymId: "paronym-1" }]);
    expect(fields.imperative).toEqual([{ imperativeId: "imperative-1" }]);
    expect(fields.synonym).toEqual([]);
  });

  test("cached and published synonym shards cannot hydrate withdrawn cards (#8714)", async () => {
    setPublishedPracticeShardsForTesting(new Set([...PUBLISHED_PRACTICE_SHARDS, "practice-synonym.A1.json"]));
    const requested: string[] = [];
    vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
      requested.push(String(input));
      return jsonResponse(404);
    });
    const fields = await fetchPracticeDrillFields("/lexicon", "A1", new Map());
    expect(fields.synonym).toEqual([]);
    expect(requested.some((url) => url.includes("practice-synonym.A1.json"))).toBe(false);

    const oldCard = { synonymId: "old-card", lemmaId: "old", targetLemmaId: "other", polarity: "synonym", prompt: "fixture", answer: "fixture", options: [], source: "fixture" } satisfies NonNullable<PracticeDeckData["synonym"]>[number];
    const deck: PracticeDeckData = { deckVersion: "old", level: "A1", index: [], lexemes: [], cloze: [], synonym: [oldCard] };
    expect(appendDrillFields(deck, { ...emptyFields, synonym: [oldCard] }).synonym).toEqual([]);
  });

  test("fetchPracticeDrillFields soft-skips 404 kinds and surfaces 5xx (#6768)", async () => {
    vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("practice-cloze.A1.json")) {
        return jsonResponse(200, { cloze: [{ clozeId: "c1" }] });
      }
      if (url.includes("practice-paronym.A1.json")) return jsonResponse(500);
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

  test("fetchPracticeDrillFields hydrates canonical imperative shard items when published", async () => {
    setPublishedPracticeShardsForTesting(
      new Set([...PUBLISHED_PRACTICE_SHARDS, "practice-imperative.A2.json"]),
    );
    const canonicalItem = {
      id: "imp_robyty_1pl",
      lemmaId: "робити",
      srsKey: "робити::imperative::1pl",
      lemma: "роби́ти",
      aspect: "imperf" as const,
      slot: "1pl" as const,
      slotLabelUa: "1-ша особа множини (заклик до дії)",
      target: "робі́мо",
      targetPlain: "робімо",
      acceptedAnswers: ["робі́мо", "робімо", "робі́м", "робім"],
      options: [
        { text: "робі́мо", isCorrect: true, code: "CORRECT" as const },
        { text: "ро́бимо", isCorrect: false, code: "WRONG_MOOD" as const },
      ],
      cefr: "A2",
    };

    vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("practice-imperative.A2.json")) {
        return jsonResponse(200, {
          schema: "atlas-practice-imperative",
          schemaVersion: 1,
          deckVersion: "v1",
          level: "A2",
          source: "vesum",
          imperative: [canonicalItem],
        });
      }
      return jsonResponse(404);
    });

    const fields = await fetchPracticeDrillFields("/lexicon", "A2", new Map());
    expect(fields.imperative).toEqual([canonicalItem]);
  });

  test("fetchPracticeDrillFields suppresses HTTP fetch for unpublished shards (#8379)", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("practice-cloze.A1.json")) {
        return jsonResponse(200, { cloze: [{ clozeId: "c1" }] });
      }
      return jsonResponse(200, {});
    });
    vi.stubGlobal("fetch", fetchMock);

    const fields = await fetchPracticeDrillFields("/lexicon", "A1", new Map());

    // Verified: imperative is NOT fetched because it is not in the pointer manifest
    const requestedUrls = fetchMock.mock.calls.map(([callUrl]) => String(callUrl));
    expect(requestedUrls.some((u) => u.includes("practice-imperative"))).toBe(false);
    expect(fields.imperative).toEqual([]);
    expect(fields.cloze).toEqual([{ clozeId: "c1" }]);
  });

  test("isPracticeShardPublished checks pointer file manifest (AC-01)", () => {
    expect(isPracticeShardPublished("practice-cloze.A1.json")).toBe(true);
    expect(isPracticeShardPublished("practice-stress.A1.json")).toBe(true);
    expect(isPracticeShardPublished("practice-paradigm.B1.json")).toBe(true);
    expect(isPracticeShardPublished("practice-imperative.A1.json")).toBe(false);
    expect(isPracticeShardPublished("practice-imperative.C1.json")).toBe(false);
  });

  test("practiceDrillShardUrls with publishedOnly=true excludes unpublished shards", () => {
    const urls = practiceDrillShardUrls("/lexicon", "A1", true);
    expect(urls.some((u) => u.includes("practice-imperative"))).toBe(false);
    expect(urls.some((u) => u.includes("practice-cloze"))).toBe(true);
  });
});


describe('public item report binding (#10704)', () => {
  afterEach(() => { vi.unstubAllGlobals(); });
  test('the real fetched bytes bind the seven fields, while mismatches, copies and mutations withhold', async () => {
    vi.stubGlobal('crypto', webcrypto);
    const text = readFileSync('public/lexicon/practice-lexemes.A1.json', 'utf8');
    vi.stubGlobal('fetch', vi.fn(async () => new Response(text)));
    const data = await getShardJson<{ lexemes: { lemmaId: string; gloss: string }[] }>('/lexicon/practice-lexemes.A1.json', new Map());
    const item = data.lexemes[0]!;
    const href = practiceReportUrl([item], 'flashcards', 'en');
    expect(href).not.toBeNull();
    const url = new URL(href!);
    expect(url.origin + url.pathname).toBe(REPORT_DESTINATION);
    expect([...url.searchParams.keys()].sort()).toEqual(['body', 'template', 'title']);
    expect(url.searchParams.get('template')).toBe('');
    const fields = Object.fromEntries(url.searchParams.get('body')!.split('\n').map((line) => {
      const [key, value] = line.split(': '); return [key, decodeURIComponent(value!)];
    }));
    expect(fields).toEqual({
      deck: 'atlas-practice-deck', version: expect.stringMatching(/^atlas-practice-v1-/),
      digest: createHash('sha256').update(text).digest('hex'), item: item.lemmaId,
      type: 'flashcards', 'interface-locale': 'en', 'public-prompt-reference-id': '/lexicon/practice-lexemes.A1.json/lexemes/0',
    });
    expect(url.searchParams.get('body')).not.toContain(item.gloss);
    expect(practiceReportUrl([{ ...item }], 'flashcards', 'en')).toBeNull();
    expect(practiceReportUrl([item], 'flashcards\nlabels: injected', 'en')).toBeNull();
    expect(practiceReportUrl([item], 'flashcards', 'en', 'private\ntext')).toBeNull();
    const changed = await parsePublicPracticeJson<typeof data>(text + ' ', '/lexicon/practice-lexemes.A1.json');
    expect(practiceReportUrl([changed.lexemes[0]!], 'flashcards', 'en')).toBeNull();
    item.gloss = 'private-learner-sentinel';
    expect(practiceReportUrl([item], 'flashcards', 'en')).toBeNull();
  });
  test('missing crypto and non-public URLs preserve practice without issuing report identities', async () => {
    vi.stubGlobal('crypto', undefined);
    const text = '[{"slug":"public-id","lemma":"fixture"}]';
    const rows = await parsePublicPracticeJson<object[]>(text, '/lexicon/daily-pool.json');
    expect(rows).toEqual([{ slug: 'public-id', lemma: 'fixture' }]);
    expect(practiceReportUrl(rows, 'daily-preview', 'en')).toBeNull();
    vi.stubGlobal('crypto', webcrypto);
    const imported = await parsePublicPracticeJson<object[]>(text, '/imports/private.json');
    expect(practiceReportUrl(imported, 'daily-preview', 'en')).toBeNull();
  });
});


describe('report consumer identities (#10704)', () => {
  afterEach(() => vi.unstubAllGlobals());
  test('a CEFR report identifies the served selection and refuses mismatched selection IDs', async () => {
    vi.stubGlobal('crypto', webcrypto);
    const lex = await parsePublicPracticeJson<{ lexemes: PracticeLexeme[] }>(readFileSync('public/lexicon/practice-lexemes.A1.json', 'utf8'), '/lexicon/practice-lexemes.A1.json');
    const index = await parsePublicPracticeJson<{ items: PracticeIndexItem[] }>(readFileSync('public/lexicon/practice-index.A1.json', 'utf8'), '/lexicon/practice-index.A1.json');
    const lemma = lex.lexemes[0]!;
    const selection: PracticeSelection = { lemma, indexItem: index.items.find((i) => i.lemmaId === lemma.lemmaId)!, mode: 'flashcards', itemId: `${lemma.lemmaId}:flashcards`, cardKey: 'private-progress-key', cardState: null, due: 0, lapsed: false, recallDirection: 'uk-to-meaning', choicePolarity: 'word-to-meaning' };
    const report = selectionReport(selection);
    expect(practiceReportUrl(report.records, report.type, 'en', report.item)).not.toBeNull();
    const matching = selectionReport({ ...selection, mode: 'matching', itemId: `${lemma.lemmaId}:matching` });
    expect(matching.type).toBe('matching-pair');
    expect(matching.item).toBe(lemma.lemmaId);
    expect(practiceReportUrl(matching.records, matching.type, 'en', matching.item)).not.toBeNull();
    expect(selectionReport({ ...selection, itemId: 'private-selection' }).records).toEqual([]);
    expect(selectionReport({ ...selection, lemma: { ...lemma, gloss: 'private' } }).records).toEqual([]);
  });
  test('teacher grammar and cloze bind the actual drill, and unknown drill IDs withhold', async () => {
    vi.stubGlobal('crypto', webcrypto);
    const deckFile = await parsePublicPracticeJson(readFileSync('public/lexicon/practice-deck.teacher.json', 'utf8'), '/lexicon/practice-deck.teacher.json');
    const clozeFile = await parsePublicPracticeJson(readFileSync('public/lexicon/practice-cloze.teacher.json', 'utf8'), '/lexicon/practice-cloze.teacher.json');
    const deck = buildTeacherDeck('virtual_teacher_table', deckFile, clozeFile);
    const grammar = [...deck.grammarById.entries()][0]!;
    const entryId = grammar[1].item.entryId;
    const entry = deck.entriesById.get(entryId)!;
    const report = teacherReport(deck, entry, { type: 'grammar', mode: grammar[1].mode, itemId: grammar[0] });
    expect(report.item).toBe(grammar[0]);
    expect(practiceReportUrl(report.records, report.type, 'en', report.item)).not.toBeNull();
    expect(teacherReport(deck, entry, { type: 'grammar', mode: 'stress', itemId: 'private-id' }).records).toEqual([]);
    const cloze = [...deck.clozeById.values()][0]!;
    const clozeEntry = deck.entriesById.get(cloze.entryId)!;
    const clozeReport = teacherReport(deck, clozeEntry, { type: 'cloze', clozeId: cloze.clozeId });
    expect(clozeReport.item).toBe(cloze.clozeId);
    expect(practiceReportUrl(clozeReport.records, clozeReport.type, 'en', clozeReport.item)).not.toBeNull();
  });
  test('pool-only daily previews bind one response and withhold copies, enrichment and changed content', async () => {
    vi.stubGlobal('crypto', webcrypto);
    const [source] = await parsePublicPracticeJson<DailyWord[]>('[{"slug":"public-item","lemma":"fixture","gloss":"public-gloss","cefr":"A1"}]', '/lexicon/daily-pool.json');
    const item: DailyPracticeDeckItem = bindDailyReport({ lemmaId: 'public-item', lemma: source!.lemma, gloss: source!.gloss, cefr: 'A1', origin: 'new', hasAtlasEntry: true, pos: null }, source!);
    expect(dailyReportRecords(item, null)).toEqual([source]);
    expect(dailyReportRecords({ ...item }, null)).toEqual([]);
    const lexeme: PracticeLexeme = { lemmaId: 'public-item', lemma: 'fixture', lemmaPlain: 'fixture', gloss: 'public-gloss', ipa: null, paradigm: { cases: {} }, pos: null, cefr: 'A1', heritage: null, severity: null };
    expect(dailyReportRecords(item, { ...lexeme, pos: 'noun' })).toEqual([]);
    item.gloss = 'private-input';
    expect(dailyReportRecords(item, null)).toEqual([]);
  });
});
