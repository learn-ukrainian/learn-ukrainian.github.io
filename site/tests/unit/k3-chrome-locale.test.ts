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

describe("K3 practice dashboard layout and copy (Chunk 2)", () => {
  const practiceSource = readFileSync(
    resolve(process.cwd(), "src/pages/words-of-the-day/practice.astro"),
    "utf8",
  );
  const lexiconPracticeSource = readFileSync(
    resolve(process.cwd(), "src/components/LexiconPractice.tsx"),
    "utf8",
  );
  const dailyDeckSource = readFileSync(
    resolve(process.cwd(), "src/components/PracticeDailyDeck.tsx"),
    "utf8",
  );

  test("practice.astro keeps the frozen K3 setup in one centered column without a filler row", () => {
    expect(practiceSource).toContain(":global(.k3-practice-dashboard) {");
    expect(practiceSource).toContain("max-width: 800px;");
    expect(practiceSource).toContain("margin: 0 auto;");
    expect(practiceSource).not.toMatch(/grid-template-areas|grid-area\s*:/);
    expect(dailyDeckSource).toContain("<details");
    expect(dailyDeckSource).toContain('onToggle={(event) => setDetailsOpen(event.currentTarget.open)}');
  });

  test("practice.astro removed the superseded static intro", () => {
    expect(practiceSource).not.toContain('<div class="lexicon-practice-intro">');
    expect(practiceSource).not.toContain('lexicon-practice-intro h1');
  });

  test("practice.astro no longer neutralizes canonical flashcard colors", () => {
    const flashcardBlock = practiceSource.match(/:global\(\.lexicon-practice-stage \.flashcard[^}]+\}/g) ?? [];
    for (const block of flashcardBlock) {
      expect(block).not.toMatch(/background\s*:\s*[^;]+important/);
      expect(block).not.toMatch(/border\s*:\s*none/);
    }
  });

  test("LexiconPractice renders the frozen single-column DOM order", () => {
    const heroIndex = lexiconPracticeSource.indexOf('className="k3-hero"');
    const statsIndex = lexiconPracticeSource.indexOf('className="k3-stats"');
    const sessionIndex = lexiconPracticeSource.indexOf('className="k3-session"');
    const wordsIndex = lexiconPracticeSource.indexOf('className="k3-words"');
    const focusIndex = lexiconPracticeSource.indexOf('className="k3-focus"');
    const modesIndex = lexiconPracticeSource.indexOf('className="k3-modes"');
    expect(heroIndex).toBeGreaterThan(0);
    expect(statsIndex).toBeGreaterThan(heroIndex);
    expect(wordsIndex).toBeGreaterThan(statsIndex);
    expect(sessionIndex).toBeGreaterThan(wordsIndex);
    expect(focusIndex).toBeGreaterThan(sessionIndex);
    expect(modesIndex).toBeGreaterThan(focusIndex);
  });

  test("mode chooser exposes all 11 modes with no icons", () => {
    expect(lexiconPracticeSource).toContain('MODE_CARD_ORDER.map');
    expect(lexiconPracticeSource).not.toContain('className="mode-card');
    expect(lexiconPracticeSource).not.toMatch(/mc-ico|ModeIcon|svg.*mode/i);
  });

  test("daily deck uses native details with aria-expanded and encoded Atlas links", () => {
    expect(dailyDeckSource).toContain('<details');
    expect(dailyDeckSource).toContain('aria-expanded={detailsOpen}');
    expect(dailyDeckSource).toContain('atlasLemmaHref(row.item.lemmaId)');
    expect(dailyDeckSource).toContain('atlasLemmaHref(currentLemmaId)');
  });
});
