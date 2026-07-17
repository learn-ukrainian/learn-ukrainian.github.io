// @vitest-environment happy-dom

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";

describe("skip-link focus-visible dismissal (K3 B3)", () => {
  test("course.css hides skip link except on :focus-visible", () => {
    const css = readFileSync(resolve(process.cwd(), "src/styles/course.css"), "utf8");
    expect(css).toMatch(/\.lu-skip-link:focus:not\(:focus-visible\)/);
    expect(css).toMatch(/\.lu-skip-link:focus-visible/);
    expect(css).not.toMatch(/\.lu-skip-link:focus\s*\{[^}]*transform:\s*translateY\(0\)/);
  });
});

describe("chrome locale block CSS (K3 A2)", () => {
  test("CourseLayout defines .lu-i18n-block show/hide rules", () => {
    const source = readFileSync(
      resolve(process.cwd(), "src/layouts/CourseLayout.astro"),
      "utf8",
    );
    expect(source).toContain(".lu-i18n-block [data-loc='uk'] { display: none; }");
    expect(source).toContain(
      "html[data-chrome-locale='uk'] .lu-i18n-block [data-loc='uk'] { display: block; }",
    );
    expect(source).toContain(
      "html[data-chrome-locale='uk'] .lu-i18n-block [data-loc='en'] { display: none; }",
    );
  });
});

describe("atlas alphabet tap targets + empty-letter filter (K3 B6/C4)", () => {
  test("AtlasFullIndex hides zero-count letters and uses 2.75rem targets", () => {
    const source = readFileSync(
      resolve(process.cwd(), "src/lexicon/AtlasFullIndex.astro"),
      "utf8",
    );
    expect(source).toContain("alphabetWithEntries");
    expect(source).toContain("(letterCounts[letter] ?? 0) > 0");
    expect(source).toContain("Showing letters that have Atlas entries.");
    expect(source).toContain("Показано літери, для яких є записи в Атласі.");
    expect(source).toMatch(/min-height:\s*2\.75rem/);
    expect(source).toMatch(/width:\s*2\.75rem/);
  });
});

describe("atlas dictionary size headline (K3 A2)", () => {
  test("lexicon landing exposes bilingual 8,206 words headline", () => {
    const source = readFileSync(
      resolve(process.cwd(), "src/pages/lexicon/index.astro"),
      "utf8",
    );
    expect(source).toContain('data-testid="atlas-dictionary-size"');
    expect(source).toContain("atlasWordsEn");
    expect(source).toContain("atlasWordsUk");
    expect(source).toContain("words");
    expect(source).toContain("слів");
  });
});
