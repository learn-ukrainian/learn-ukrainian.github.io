import { describe, expect, test } from "vitest";
import {
  PRACTICE_LEVELS,
  buildLexiconApiContract,
  buildLexiconRuntimeStatus,
  type PracticeLevel,
} from "@site/src/lib/lexicon/runtime-contract";
import type { AtlasEntryModelCounts } from "@site/src/lib/lexicon/atlasDb";

function entryModel(overrides: Partial<AtlasEntryModelCounts> = {}): AtlasEntryModelCounts {
  return {
    reviewed_entries_by_type: {
      lemma: 3,
      expression: 0,
      phraseologism: 0,
      proverb: 0,
      multiword_term: 0,
      proper_name: 0,
    },
    total_reviewed_entries: 3,
    alias_records: 1,
    candidate_evidence_count: 0,
    candidate_evidence_by_bucket: {},
    noise_rejected: 0,
    ...overrides,
  };
}

function practiceIndexes(overrides: Partial<Record<PracticeLevel, unknown>> = {}) {
  return Object.fromEntries(
    PRACTICE_LEVELS.map((level) => [
      level,
      {
        deckVersion: "atlas-practice-v1-test",
        counts: {
          lexemes: level === "A1" ? 2 : 0,
          cloze: level === "A1" ? 1 : 0,
          clozeEligibleLexemes: level === "A1" ? 1 : 0,
          clozeCoverage: level === "A1" ? 0.5 : 0,
        },
        ...((overrides[level] as Record<string, unknown> | undefined) ?? {}),
      },
    ]),
  ) as Record<PracticeLevel, unknown>;
}

describe("buildLexiconRuntimeStatus", () => {
  test("summarizes the static Atlas contract", () => {
    const status = buildLexiconRuntimeStatus({
      generatedAt: "2026-06-30T00:00:00.000Z",
      manifest: {
        version: "0.1",
        generated_at: "2026-06-29T00:00:00Z",
        entries: [
          { lemma: "дім", url_slug: "дім", primary_source: "built_vocabulary" },
          { lemma: "ананас", url_slug: "ананас", primary_source: "source_inventory_grow" },
          {
            lemma: "тигр",
            url_slug: "тигр",
            primary_source: "source_inventory_grow",
            surface_admission: { daily: true, practice: false, cloze: false },
          },
          { lemma: "pluralia tantum", url_slug: "pluralia-tantum", pos: "grammar term" },
        ],
      },
      manifestPointer: {
        release_tag: "atlas-manifest",
        json_bytes: 42,
        json_sha256: "abc123",
      },
      searchIndex: [{ l: "дім" }, { l: "ананас" }, { l: "тигр" }],
      searchAliases: [{ a: "дому", s: "дім", h: "дім", k: "inflected_form" }],
      searchShards: {
        prefixMap: { а: "u0430", д: "u0434" },
        shards: {
          u0430: { path: "/lexicon/search/u0430.json" },
          u0434: { path: "/lexicon/search/u0434.json" },
        },
      },
      browseMeta: {
        total: 3,
        letterCounts: { А: 2, Д: 1, И: 0 },
      },
      entryModel: entryModel(),
      dailyPool: [{ lemma: "дім" }],
      practiceIndexes: practiceIndexes(),
      clozeSources: [{ lemma: "дім" }],
      reviewedSources: { reviewed: [{ path: "curriculum/l2-uk-en/a1/vocabulary.yaml" }] },
    });

    expect(status.schema).toBe("atlas-runtime-status");
    expect(status.status).toBe("ok");
    expect(status.manifest.records).toBe(4);
    expect(status.manifest.publicLexemeRecords).toBe(3);
    expect(status.manifest.grammarTermRecords).toBe(1);
    expect(status.publicAtlas.searchArticleEntries).toBe(3);
    expect(status.publicAtlas.searchAliasRows).toBe(1);
    expect(status.publicAtlas.searchShards).toBe(2);
    expect(status.publicAtlas.searchShardPrefixes).toBe(2);
    expect(status.publicAtlas.browseRecords).toBe(3);
    expect(status.publicAtlas.browseShards).toBe(2);
    expect(status.endpoints.contract).toBe("/api/lexicon/contract.json");
    expect(status.daily.poolEntries).toBe(1);
    expect(status.practice.totalLexemes).toBe(2);
    expect(status.cloze.totalItems).toBe(1);
    expect(status.cloze.sourceRows).toBe(1);
    expect(status.cloze.reviewedSourceRows).toBe(1);
    expect(status.sourceInventory.atlasRows).toBe(2);
    expect(status.sourceInventory.dailyAdmitted).toBe(1);
    expect(status.sourceInventory.practiceAdmitted).toBe(0);
    expect(status.entryModel.reviewed_entries_by_type.lemma).toBe(3);
    expect(status.entryModel.total_reviewed_entries).toBe(3);
    expect(status.entryModel.alias_records).toBe(1);
    expect(status.entryModel.candidate_evidence_count).toBe(0);
    expect(status.checks.searchMatchesReviewedEntries).toBe(true);

    const contract = buildLexiconApiContract(status);
    expect(contract.schema).toBe("atlas-api-contract");
    expect(contract.staticOnly).toBe(true);
    expect(contract.surfaces.atlas.totalReviewedEntries).toBe(3);
    expect(contract.surfaces.atlas.reviewedEntriesByType.lemma).toBe(3);
    expect(contract.surfaces.atlas.aliasRecords).toBe(1);
    expect(contract.surfaces.atlas.candidateEvidenceCount).toBe(0);
    expect(contract.surfaces.dailyWord.poolEntries).toBe(1);
    expect(contract.surfaces.dailyWord.admission).toBe("reviewed-static-pool");
    expect(contract.surfaces.practice.totalLexemes).toBe(2);
    expect(contract.surfaces.practice.levels).toEqual([...PRACTICE_LEVELS]);
    expect(contract.surfaces.cloze.totalItems).toBe(1);
    expect(contract.endpoints.contract).toBe("/api/lexicon/contract.json");
  });

  test("warns when static surfaces drift", () => {
    const status = buildLexiconRuntimeStatus({
      manifest: {
        entries: [{ lemma: "дім", url_slug: "дім" }],
      },
      manifestPointer: {},
      searchIndex: [{ l: "дім" }, { l: "кава" }],
      searchAliases: [],
      browseMeta: { total: 1, letterCounts: { Д: 1 } },
      entryModel: entryModel({ total_reviewed_entries: 1 }),
      dailyPool: [],
      practiceIndexes: practiceIndexes({
        A2: { deckVersion: "atlas-practice-v1-other", counts: { lexemes: 1 } },
      }),
      clozeSources: [],
      reviewedSources: { reviewed: [] },
    });

    expect(status.status).toBe("warning");
    expect(status.checks.searchMatchesReviewedEntries).toBe(false);
    expect(status.checks.singlePracticeDeckVersion).toBe(false);
  });
});
