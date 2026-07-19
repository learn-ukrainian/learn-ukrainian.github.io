// @vitest-environment happy-dom

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";
import { GET as getDailyPool } from "@site/src/pages/api/lexicon/daily-pool.json";
import type { DailyWord } from "@site/src/lib/lexicon/daily";

const dailyWordsSource = readFileSync(
  resolve(process.cwd(), "src/lexicon/DailyWords.astro"),
  "utf8",
);

describe("DailyWords list example sentence (GH #5434)", () => {
  test("DailyWords Astro renders an example slot with bilingual scaffolding", () => {
    expect(dailyWordsSource).toContain("word.example?.trim()");
    expect(dailyWordsSource).toContain('data-testid="daily-example-');
    expect(dailyWordsSource).toContain('class="lexicon-daily-example"');
    expect(dailyWordsSource).toContain('class="lexicon-daily-example-en"');
    expect(dailyWordsSource).toContain('lang="uk"');
    expect(dailyWordsSource).toContain('lang="en"');
  });

  test("DailyWords card omits example markup when no example is present", () => {
    // renderExample returns an empty string for missing data, so the card does
    // not create an empty element.
    expect(dailyWordsSource).toContain("if (!example) return \"\";");
  });

  test("daily pool API route exposes optional example fields", async () => {
    const response = await getDailyPool({} as Parameters<typeof getDailyPool>[0]);
    const pool = (await response.json()) as DailyWord[];

    expect(Array.isArray(pool)).toBe(true);
    expect(pool.length).toBeGreaterThan(0);

    // Schema is permissive: examples may not be populated yet, but every row
    // must remain a valid DailyWord with the new optional fields.
    for (const row of pool) {
      expect(row).toHaveProperty("lemma");
      expect(row).toHaveProperty("slug");
      expect(row).toHaveProperty("gloss");
      if (row.example !== undefined && row.example !== null) {
        expect(typeof row.example).toBe("string");
        expect(row.example.trim()).toBe(row.example);
      }
      if (row.exampleEn !== undefined && row.exampleEn !== null) {
        expect(typeof row.exampleEn).toBe("string");
        expect(row.exampleEn.trim()).toBe(row.exampleEn);
      }
    }
  });
});
