// @vitest-environment happy-dom

/**
 * PR3 slice 1 — normalized DOM parity: reference Astro HTML fixtures (captured
 * from main pre-port) vs React WordAtlasArticle SSR for every fixture entry type.
 */
import Database from "better-sqlite3";
import { buildWordAtlasArticleView } from "@site/src/lib/lexicon/word-atlas-article-model";
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

// Frozen report expectations: thin_page_report.py, unchanged fixture bytes.
const THIN_FIXTURES: Record<string, number> = {
  "будь-ласка": 3, "доконаний-вид": 1, "fixture-expression": 1,
  "fixture-phraseologism": 1, "fixture-proverb": 1, "fixture-proper-name": 1,
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

      let left = normalizeArticleDom(referenceHtml);
      let right = normalizeArticleDom(reactHtml);
      if (meta.slug in THIN_FIXTURES) {
        const model = buildWordAtlasArticleView(result.record, catalog.generatedAt, catalog.manifestVersion);
        expect(model.renderedTier).toEqual({ tier: "thin", richBuckets: THIN_FIXTURES[meta.slug] });
        const reference = new DOMParser().parseFromString(referenceHtml, "text/html");
        const rendered = new DOMParser().parseFromString(reactHtml, "text/html");
        const note = rendered.querySelector(".atlas-enrichment-note");
        expect(note?.getAttribute("data-atlas-tier")).toBe("thin");
        expect(note?.querySelector("p [data-loc=en]")?.textContent).toBe("This entry is being enriched.");
        expect(note?.querySelector("p [data-loc=uk]")?.textContent).toBe("Стаття доповнюється.");
        expect(note?.querySelector("[aria-live], [role=status]")).toBeNull();
        const waiting = Array.from(reference.querySelectorAll(".atlas-overview-card.pending"))
          .filter((card) => !["Курс", "Стилістика", "Зовнішні"].includes(card.querySelector(".overview-label")?.textContent?.trim() ?? ""))
          .map((card) => card.querySelector(".overview-label")?.textContent?.trim());
        expect(Array.from(note?.querySelectorAll("li [data-loc=uk]") ?? []).map((item) => item.textContent)).toEqual(waiting);
        expect(rendered.querySelectorAll(".atlas-overview-card.pending")).toHaveLength(0);
        // Only these six approved overview/note regions may differ. All source
        // content, component links, Practice CTA and unavailable hint stay exact.
        for (const card of reference.querySelectorAll(".atlas-overview-card.pending")) card.remove();
        note?.remove();
        left = normalizeArticleDom(reference.body.innerHTML);
        right = normalizeArticleDom(rendered.body.innerHTML);
      }
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


// Optional live-reference proof uses real public article payloads, never synthetic
// substitutes. The required worker run supplies ATLAS_REFERENCE_DB_PATH; CI keeps
// the tracked six-fixture denominator above. Missing live data fails this run.
if (process.env.ATLAS_REFERENCE_DB_PATH) {
  describe("nine report references: actual payload tier and render parity (#8327)", () => {
    const references = [
      ["кричачи", "bare", 2], ["найактивніше", "bare", 2], ["самолікуватися", "bare", 1],
      ["абак", "thin", 4], ["абака", "thin", 2], ["аби-то", "thin", 4],
      ["а", "rich", 6], ["абажур", "rich", 5], ["абат", "rich", 5],
    ] as const;
    for (const [slug, tier, richBuckets] of references) {
      test(`${slug}: report ${tier}/${richBuckets}`, async () => {
        const db = new Database(process.env.ATLAS_REFERENCE_DB_PATH!, { readonly: true, fileMustExist: true });
        let row: { payload_json: string; entry_type: string } | undefined;
        try {
          row = db.prepare("SELECT p.payload_json, a.entry_type FROM article_payloads p JOIN articles a ON a.slug=p.slug WHERE a.slug=? AND a.visibility='public'")
            .get(slug) as typeof row;
        } finally { db.close(); }
        expect(row, `actual reference unavailable: ${slug}`).toBeDefined();
        const entry = { ...JSON.parse(row!.payload_json), entry_type: row!.entry_type };
        const record = { slug, kind: "article" as const, entry, aliases: [], relations: [], provenance: [],
          renderContext: { componentLinks: [], practiceLevels: [] } };
        const model = buildWordAtlasArticleView(record, "test", "test");
        expect(model.renderedTier).toEqual({ tier, richBuckets });
        const doc = new DOMParser().parseFromString(renderWordAtlasArticle({ record, generatedAt: "test", manifestVersion: "test" }), "text/html");
        expect(doc.querySelectorAll(".atlas-enrichment-note")).toHaveLength(tier === "rich" ? 0 : 1);
        expect(doc.querySelectorAll(".atlas-overview-card.ready")).toHaveLength(model.articleOverview.filter((card) => card.ready).length);
        for (const section of doc.querySelectorAll("section.atlas-section")) {
          const heading = section.querySelector("h2");
          if (!heading) continue;
          const content = section.cloneNode(true) as Element;
          content.querySelector("h2")?.remove();
          expect(content.textContent?.trim().length, `${slug}: empty heading ${heading.textContent}`).toBeGreaterThan(0);
        }
      });
    }
  });
}
