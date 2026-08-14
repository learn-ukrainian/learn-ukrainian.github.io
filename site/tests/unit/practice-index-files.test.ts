import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, test } from "vitest";
import {
  practiceIndexCandidatePaths,
  readPracticeIndexItems,
} from "@site/src/lib/lexicon/practice-index-files";

describe("practice-index-files", () => {
  test("lists canonical /lexicon path before /api/lexicon alias", () => {
    const paths = practiceIndexCandidatePaths("/tmp/data", "A1");
    expect(paths[0]).toContain("/site/public/lexicon/practice-index.A1.json");
    expect(paths[1]).toContain("/site/public/api/lexicon/practice-index.A1.json");
  });

  test("prefers canonical lexicon shard when both exist", () => {
    const root = mkdtempSync(join(tmpdir(), "practice-index-"));
    const dbDir = join(root, "data");
    mkdirSync(dbDir);
    const lexiconDir = join(root, "site/public/lexicon");
    const apiDir = join(root, "site/public/api/lexicon");
    mkdirSync(lexiconDir, { recursive: true });
    mkdirSync(apiDir, { recursive: true });
    writeFileSync(
      join(lexiconDir, "practice-index.A1.json"),
      JSON.stringify({ items: [{ lemmaId: "canonical" }] }),
    );
    writeFileSync(
      join(apiDir, "practice-index.A1.json"),
      JSON.stringify({ items: [{ lemmaId: "alias" }] }),
    );

    expect(readPracticeIndexItems(dbDir, "A1")).toEqual([{ lemmaId: "canonical" }]);
  });

  test("falls back to /api/lexicon alias when canonical is missing", () => {
    const root = mkdtempSync(join(tmpdir(), "practice-index-"));
    const dbDir = join(root, "data");
    mkdirSync(dbDir);
    const apiDir = join(root, "site/public/api/lexicon");
    mkdirSync(apiDir, { recursive: true });
    writeFileSync(
      join(apiDir, "practice-index.B1.json"),
      JSON.stringify({ items: [{ lemmaId: "alias-only" }] }),
    );

    expect(readPracticeIndexItems(dbDir, "B1")).toEqual([{ lemmaId: "alias-only" }]);
  });

  test("returns null when no candidate resolves", () => {
    const root = mkdtempSync(join(tmpdir(), "practice-index-"));
    const dbDir = join(root, "data");
    mkdirSync(dbDir);
    expect(readPracticeIndexItems(dbDir, "C1")).toBeNull();
  });
});
