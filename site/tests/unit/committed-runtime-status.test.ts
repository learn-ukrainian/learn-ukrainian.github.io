import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { afterEach, beforeEach, describe, expect, test } from "vitest";

import {
  buildCommittedLexiconRuntimeStatus,
  resetCommittedLexiconRuntimeStatusForTests,
} from "../../src/lib/lexicon/committed-runtime-status";

const TEST_FIXTURE_BASE = resolve(process.cwd(), "tests/fixtures/tmp-runtime-status");

function createFixtureRoot(
  name: string,
  options: {
    hasManifest?: boolean;
    dailyCount?: number;
  } = {},
): string {
  const root = resolve(TEST_FIXTURE_BASE, name);
  const { hasManifest = true, dailyCount = 1 } = options;

  const manifest = {
    version: "local-v2",
    generated_at: "2026-10-12T00:00:00Z",
    entries: [
      {
        lemma: "слово",
        url_slug: "slovo",
        primary_source: "source_inventory_grow",
        surface_admission: { daily: true, practice: true, cloze: true },
      },
      {
        lemma: "граматика",
        url_slug: "hramatyka",
        pos: "grammar term",
      },
    ],
  };

  const files: Record<string, unknown> = {
    "src/data/lexicon-manifest.pointer.json": {
      manifest_version: "release-v1",
      generated_at: "2026-09-01T00:00:00Z",
      release_tag: "atlas-manifest-v1",
      json_bytes: 1000,
      json_sha256: "dummy-sha",
    },
    "src/data/lexicon-search-index.json": [{ t: "lemma" }],
    "src/data/lexicon-search-aliases.json": [],
    "src/data/lexicon-search-shards.json": {},
    "src/data/lexicon-browse-meta.json": { total: 1, letterCounts: { С: 1 } },
    "src/data/lexicon-daily-pool.json": Array.from({ length: dailyCount }, (_, i) => ({ id: i })),
    "src/data/lexicon-practice-cloze-sources.json": [],
    "src/data/lexicon-practice-reviewed-sources.json": [],
    "public/lexicon/practice-index.A1.json": {
      deckVersion: "v1",
      counts: { lexemes: 1, cloze: 1 },
    },
  };

  if (hasManifest) {
    files["src/data/lexicon-manifest.json"] = manifest;
  }

  for (const [relativePath, content] of Object.entries(files)) {
    const fullPath = resolve(root, relativePath);
    mkdirSync(dirname(fullPath), { recursive: true });
    writeFileSync(fullPath, JSON.stringify(content));
  }

  return root;
}

describe("committed lexicon runtime status", () => {
  beforeEach(() => {
    resetCommittedLexiconRuntimeStatusForTests();
  });

  afterEach(() => {
    resetCommittedLexiconRuntimeStatusForTests();
    rmSync(TEST_FIXTURE_BASE, { recursive: true, force: true });
  });

  test("returns hydrated status and non-null source inventory when manifest is present", () => {
    const root = createFixtureRoot("hydrated", { hasManifest: true });
    const status = buildCommittedLexiconRuntimeStatus(root);

    expect(status.manifest.hydrated).toBe(true);
    expect(status.manifest.records).toBe(2);
    expect(status.manifest.publicLexemeRecords).toBe(1);
    expect(status.manifest.grammarTermRecords).toBe(1);
    expect(status.manifest.version).toBe("local-v2");
    expect(status.manifest.generatedAt).toBe("2026-10-12T00:00:00Z");

    expect(status.sourceInventory.atlasRows).toBe(1);
    expect(status.sourceInventory.dailyAdmitted).toBe(1);
    expect(status.sourceInventory.practiceAdmitted).toBe(1);
    expect(status.sourceInventory.clozeAdmitted).toBe(1);
  });

  test("falls back to pointer and null source inventory when manifest is absent", () => {
    const root = createFixtureRoot("unhydrated", { hasManifest: false });
    const status = buildCommittedLexiconRuntimeStatus(root);

    expect(status.manifest.hydrated).toBe(false);
    expect(status.manifest.records).toBeNull();
    expect(status.manifest.publicLexemeRecords).toBeNull();
    expect(status.manifest.grammarTermRecords).toBeNull();
    expect(status.manifest.version).toBe("release-v1");
    expect(status.manifest.generatedAt).toBe("2026-09-01T00:00:00Z");

    expect(status.sourceInventory.atlasRows).toBeNull();
    expect(status.sourceInventory.dailyAdmitted).toBeNull();
    expect(status.sourceInventory.practiceAdmitted).toBeNull();
    expect(status.sourceInventory.clozeAdmitted).toBeNull();
  });

  test("isolates cache across different roots and supports test cache reset", () => {
    const rootA = createFixtureRoot("root-a", { dailyCount: 1 });
    const rootB = createFixtureRoot("root-b", { dailyCount: 3 });

    const statusA1 = buildCommittedLexiconRuntimeStatus(rootA);
    const statusB = buildCommittedLexiconRuntimeStatus(rootB);
    const statusA2 = buildCommittedLexiconRuntimeStatus(rootA);

    expect(statusA1.daily.poolEntries).toBe(1);
    expect(statusB.daily.poolEntries).toBe(3);
    expect(statusA2.daily.poolEntries).toBe(1);

    expect(statusA1).toBe(statusA2);
    expect(statusA1).not.toBe(statusB);

    resetCommittedLexiconRuntimeStatusForTests();
    const statusA3 = buildCommittedLexiconRuntimeStatus(rootA);
    expect(statusA3).not.toBe(statusA1);
    expect(statusA3.daily.poolEntries).toBe(1);
  });
});
