// Matches the committed static practice shard set and
// scripts/audit/check_static_practice_assets.py::DEFAULT_LEVELS.
export const PRACTICE_LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;

export type PracticeLevel = (typeof PRACTICE_LEVELS)[number];

type JsonObject = Record<string, unknown>;

export interface LexiconRuntimeStatus {
  schema: "atlas-runtime-status";
  schemaVersion: 1;
  generatedAt: string;
  status: "ok" | "warning";
  endpoints: {
    status: string;
    searchIndex: string;
    dailyPool: string;
    browseShardTemplate: string;
    practiceIndexTemplate: string;
    practiceLexemesTemplate: string;
    practiceClozeTemplate: string;
  };
  manifest: {
    hydrated: boolean;
    entries: number | null;
    publicLexemes: number | null;
    grammarTermRows: number | null;
    version: string | null;
    releaseTag: string | null;
    generatedAt: string | null;
    jsonBytes: number | null;
    jsonSha256: string | null;
  };
  publicAtlas: {
    searchEntries: number;
    browseEntries: number;
    browseShards: number;
    browseLetters: number;
  };
  daily: {
    poolEntries: number;
  };
  practice: {
    totalLexemes: number;
    deckVersions: string[];
    levels: Record<PracticeLevel, PracticeLevelStatus>;
  };
  cloze: {
    totalItems: number;
    sourceRows: number;
    reviewedSourceRows: number;
  };
  sourceInventory: {
    atlasRows: number | null;
    dailyAdmitted: number | null;
    practiceAdmitted: number | null;
    clozeAdmitted: number | null;
  };
  checks: {
    searchMatchesBrowse: boolean;
    manifestCoversPublic: boolean | null;
    singlePracticeDeckVersion: boolean;
  };
}

export interface PracticeLevelStatus {
  lexemes: number;
  cloze: number;
  clozeEligibleLexemes: number;
  clozeCoverage: number;
}

interface BuildRuntimeStatusInput {
  generatedAt?: string;
  manifest?: unknown;
  manifestPointer?: unknown;
  searchIndex?: unknown;
  browseMeta?: unknown;
  dailyPool?: unknown;
  practiceIndexes?: Partial<Record<PracticeLevel, unknown>>;
  clozeSources?: unknown;
  reviewedSources?: unknown;
}

function asObject(value: unknown): JsonObject {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as JsonObject)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function asOptionalNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function manifestEntries(manifest: unknown): JsonObject[] | null {
  const payload = asObject(manifest);
  const entries = asArray(payload.entries);
  if (!entries.length) return null;
  return entries.filter((entry): entry is JsonObject => {
    return Boolean(entry) && typeof entry === "object" && !Array.isArray(entry);
  });
}

function surfaceAdmission(entry: JsonObject, surface: "daily" | "practice" | "cloze"): boolean {
  return asObject(entry.surface_admission)[surface] === true;
}

function practiceLevelStatus(indexPayload: unknown): PracticeLevelStatus {
  const index = asObject(indexPayload);
  const counts = asObject(index.counts);
  return {
    lexemes: asNumber(counts.lexemes),
    cloze: asNumber(counts.cloze),
    clozeEligibleLexemes: asNumber(counts.clozeEligibleLexemes),
    clozeCoverage: asNumber(counts.clozeCoverage),
  };
}

function reviewedSourceCount(payload: unknown): number {
  const obj = asObject(payload);
  if (Array.isArray(obj.reviewed)) return obj.reviewed.length;
  return asArray(payload).length;
}

export function buildLexiconRuntimeStatus(input: BuildRuntimeStatusInput): LexiconRuntimeStatus {
  const entries = manifestEntries(input.manifest);
  const manifest = asObject(input.manifest);
  const pointer = asObject(input.manifestPointer);
  const searchEntries = asArray(input.searchIndex).length;
  const browseMeta = asObject(input.browseMeta);
  const letterCounts = asObject(browseMeta.letterCounts);
  const browseEntries = asNumber(browseMeta.total);
  const browseLetters = Object.keys(letterCounts).length;
  const browseShards = Object.values(letterCounts).filter((count) => asNumber(count) > 0).length;
  const dailyPoolEntries = asArray(input.dailyPool).length;
  const practiceLevels = {} as Record<PracticeLevel, PracticeLevelStatus>;
  const deckVersions = new Set<string>();

  for (const level of PRACTICE_LEVELS) {
    const index = asObject(input.practiceIndexes?.[level]);
    practiceLevels[level] = practiceLevelStatus(index);
    const deckVersion = asString(index.deckVersion);
    if (deckVersion) deckVersions.add(deckVersion);
  }

  const totalPracticeLexemes = Object.values(practiceLevels).reduce(
    (sum, row) => sum + row.lexemes,
    0,
  );
  const totalCloze = Object.values(practiceLevels).reduce((sum, row) => sum + row.cloze, 0);
  const publicLexemes = entries
    ? entries.filter((entry) => entry.pos !== "grammar term").length
    : null;
  const sourceInventoryRows = entries
    ? entries.filter((entry) => entry.primary_source === "source_inventory_grow")
    : null;
  const searchMatchesBrowse = searchEntries === browseEntries;
  const manifestCoversPublic =
    publicLexemes === null ? null : publicLexemes === searchEntries && publicLexemes === browseEntries;
  const singlePracticeDeckVersion = deckVersions.size <= 1;
  const status =
    searchMatchesBrowse &&
    (manifestCoversPublic ?? true) &&
    singlePracticeDeckVersion &&
    dailyPoolEntries > 0 &&
    totalPracticeLexemes > 0
      ? "ok"
      : "warning";

  return {
    schema: "atlas-runtime-status",
    schemaVersion: 1,
    generatedAt: input.generatedAt ?? new Date().toISOString(),
    status,
    endpoints: {
      status: "/api/lexicon/status.json",
      searchIndex: "/api/lexicon/search-index.json",
      dailyPool: "/api/lexicon/daily-pool.json",
      browseShardTemplate: "/lexicon/browse/{letter}.json",
      practiceIndexTemplate: "/api/lexicon/practice-index.{level}.json",
      practiceLexemesTemplate: "/api/lexicon/practice-lexemes.{level}.json",
      practiceClozeTemplate: "/api/lexicon/practice-cloze.{level}.json",
    },
    manifest: {
      hydrated: entries !== null,
      entries: entries?.length ?? null,
      publicLexemes,
      grammarTermRows: entries && publicLexemes !== null ? entries.length - publicLexemes : null,
      version: asString(manifest.version) ?? asString(pointer.manifest_version),
      releaseTag: asString(pointer.release_tag),
      generatedAt: asString(manifest.generated_at) ?? asString(pointer.generated_at),
      jsonBytes: asOptionalNumber(pointer.json_bytes),
      jsonSha256: asString(pointer.json_sha256),
    },
    publicAtlas: {
      searchEntries,
      browseEntries,
      browseShards,
      browseLetters,
    },
    daily: {
      poolEntries: dailyPoolEntries,
    },
    practice: {
      totalLexemes: totalPracticeLexemes,
      deckVersions: [...deckVersions].sort(),
      levels: practiceLevels,
    },
    cloze: {
      totalItems: totalCloze,
      sourceRows: asArray(input.clozeSources).length,
      reviewedSourceRows: reviewedSourceCount(input.reviewedSources),
    },
    sourceInventory: {
      atlasRows: sourceInventoryRows?.length ?? null,
      dailyAdmitted: sourceInventoryRows?.filter((entry) => surfaceAdmission(entry, "daily")).length ?? null,
      practiceAdmitted:
        sourceInventoryRows?.filter((entry) => surfaceAdmission(entry, "practice")).length ?? null,
      clozeAdmitted: sourceInventoryRows?.filter((entry) => surfaceAdmission(entry, "cloze")).length ?? null,
    },
    checks: {
      searchMatchesBrowse,
      manifestCoversPublic,
      singlePracticeDeckVersion,
    },
  };
}
