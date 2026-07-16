// @vitest-environment happy-dom

/**
 * PR3 slice 1 — normalized DOM parity: reference Astro HTML fixtures (captured
 * from main pre-port) vs React WordAtlasArticle SSR for every fixture entry type.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { beforeAll, describe, expect, test } from "vitest";
import {
  resetSqliteAtlasDataSourceCachesForTests,
  SqliteAtlasDataSource,
} from "@site/src/lib/lexicon/sqlite-atlas-data-source";
import { renderWordAtlasArticle } from "../helpers/render-word-atlas-article";
import { normalizeArticleDom } from "../helpers/normalize-article-dom";

const FIXTURE_DB = resolve(
  process.env.ATLAS_DB_PATH ??
    resolve(process.cwd(), "../tests/fixtures/atlas/runtime_shards_fixture.db"),
);
const REF_DIR = resolve(process.cwd(), "tests/fixtures/atlas-article-reference");
const MANIFEST = JSON.parse(
  readFileSync(resolve(REF_DIR, "manifest.json"), "utf8"),
) as {
  slugs: Array<{ slug: string; file: string; entry_type: string; kind: string }>;
};

describe("WordAtlasArticle normalized DOM parity (PR3)", () => {
  let source: SqliteAtlasDataSource;
  let catalog: ReturnType<SqliteAtlasDataSource["getStaticCatalog"]>;

  beforeAll(() => {
    process.env.ATLAS_DB_PATH = FIXTURE_DB;
    process.env.ATLAS_MANIFEST_ALLOW_STALE_POINTER = "1";
    resetSqliteAtlasDataSourceCachesForTests();
    source = new SqliteAtlasDataSource();
    catalog = source.getStaticCatalog();
  });

  test("reference manifest covers all required entry types", () => {
    const types = new Set(MANIFEST.slugs.map((s) => s.entry_type));
    for (const required of [
      "lemma",
      "expression",
      "phraseologism",
      "proverb",
      "multiword_term",
      "proper_name",
      "form_route",
    ]) {
      expect(types.has(required), `missing entry_type ${required}`).toBe(true);
    }
  });

  for (const meta of MANIFEST.slugs) {
    test(`normalized DOM matches reference for ${meta.slug} (${meta.entry_type})`, async () => {
      const result = await source.getEntry(meta.slug, {
        expectedVersion: catalog.sourceVersion,
      });
      expect(result.kind).toBe("entry");
      if (result.kind !== "entry") return;

      const reactHtml = renderWordAtlasArticle({
        record: result.record,
        generatedAt: catalog.generatedAt,
        manifestVersion: catalog.manifestVersion,
      });
      const referenceHtml = readFileSync(resolve(REF_DIR, meta.file), "utf8");

      const left = normalizeArticleDom(referenceHtml);
      const right = normalizeArticleDom(reactHtml);
      if (left !== right) {
        const leftLines = left.split("\n");
        const rightLines = right.split("\n");
        const diffs: string[] = [];
        const n = Math.max(leftLines.length, rightLines.length);
        for (let i = 0; i < n; i += 1) {
          if (leftLines[i] !== rightLines[i]) {
            diffs.push(`@@ line ${i + 1}`);
            if (leftLines[i] !== undefined) diffs.push(`- ${leftLines[i]}`);
            if (rightLines[i] !== undefined) diffs.push(`+ ${rightLines[i]}`);
            if (diffs.length > 40) {
              diffs.push("... truncated ...");
              break;
            }
          }
        }
        expect.soft(right, diffs.join("\n")).toBe(left);
      }
      expect(right).toBe(left);
    });
  }
});

describe("normalizeArticleDom entity handling (CodeQL js/double-escaping regression)", () => {
  test("literal '&lt;' text is NOT equated with a real '<' character", () => {
    // Source `&amp;lt;` parses to the literal characters `&lt;`; source `&lt;`
    // parses to `<`. These are genuinely different renders and the parity
    // gate must keep them distinct (no second decode pass after DOMParser).
    const literalAmp = normalizeArticleDom(
      '<div data-word-atlas><p>&amp;lt;слово&amp;gt;</p></div>',
    );
    const realAngle = normalizeArticleDom(
      "<div data-word-atlas><p>&lt;слово&gt;</p></div>",
    );
    expect(literalAmp).not.toBe(realAngle);
    expect(literalAmp).toContain("&lt;слово&gt;");
    expect(realAngle).toContain("<слово>");
  });

  test("parser-decoded quote entities still normalize identically", () => {
    // `&#x27;` and a raw apostrophe are identical AFTER the single DOMParser
    // decode — removing the second decode pass must not break this.
    const encoded = normalizeArticleDom(
      "<div data-word-atlas><p>п&#x27;ять</p></div>",
    );
    const raw = normalizeArticleDom("<div data-word-atlas><p>п'ять</p></div>");
    expect(encoded).toBe(raw);
  });
});
