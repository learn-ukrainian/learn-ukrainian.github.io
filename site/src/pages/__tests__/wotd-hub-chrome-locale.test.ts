// @vitest-environment happy-dom
/**
 * #6711 — WotD hub chrome must follow the en/uk toggle (chrome only, never content).
 * Readings hero/search half was fixed in #6750; this covers the leftover hub body.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";
import {
  CHROME_STRINGS,
  chromeDualHtml,
  formatWotdEmptyLevel,
  formatWotdLevelCount,
} from "@site/src/lib/i18n/chrome";

const root = process.cwd();
const wotdHub = readFileSync(resolve(root, "src/pages/words-of-the-day.astro"), "utf8");
const dailyWords = readFileSync(resolve(root, "src/lexicon/DailyWords.astro"), "utf8");
const readingsIndex = readFileSync(resolve(root, "src/pages/readings/index.astro"), "utf8");
const chromeDict = readFileSync(resolve(root, "src/lib/i18n/chrome.ts"), "utf8");

describe("readings chrome locale (#6750 already on HEAD)", () => {
  test("readings index wires hero + search through Chrome Locale Runtime", () => {
    expect(readingsIndex).toContain('titleKey="nav.readings"');
    expect(readingsIndex).toContain('subtitleKey="readings.subtitle"');
    expect(readingsIndex).toContain("data-i18n-placeholder");
    expect(readingsIndex).toContain("readings.searchPlaceholder");
  });
});

describe("WotD hub chrome locale (#6711)", () => {
  test("hub hero dual-renders title, subtitle, badge, and practice CTA via ChromeText", () => {
    expect(wotdHub).toContain("ChromeText");
    expect(wotdHub).toMatch(/ChromeText\s+k="nav\.dailyWords"/);
    expect(wotdHub).toMatch(/ChromeText\s+k="wotd\.subtitle"/);
    expect(wotdHub).toMatch(/ChromeText\s+k="wotd\.practiceCta"/);
    // No slash-dual leftovers (#5503) and no Ukrainian-only hero chrome.
    expect(wotdHub).not.toContain("Слова дня / Words of the Day");
    expect(wotdHub).not.toMatch(/<h1[^>]*>\s*Слова дня/);
    expect(wotdHub).not.toContain("Практика — інтервальне повторення вашого рівня →");
  });

  test("DailyWords section chrome uses ChromeText / dual-render, not Ukrainian-only literals", () => {
    expect(dailyWords).toContain("ChromeText");
    expect(dailyWords).toMatch(/ChromeText\s+k="wotd\.todayTitle"/);
    expect(dailyWords).toMatch(/ChromeText\s+k="wotd\.todayDescription"/);
    expect(dailyWords).toMatch(/ChromeText\s+k="practice\.level"/);
    expect(dailyWords).toMatch(/ChromeText\s+k="wotd\.loading"/);
    expect(dailyWords).toMatch(/ChromeText\s+k="wotd\.loadError"/);
    expect(dailyWords).toMatch(/ChromeText\s+k="practice\.retry"/);
    expect(dailyWords).not.toContain(">Добірка на сьогодні<");
    expect(dailyWords).not.toContain(">Рівень<");
    expect(dailyWords).not.toContain("Завантажуємо добірку...");
    expect(dailyWords).not.toContain("${activeLevel} · ${picks.length} слів");
  });

  test("dictionary holds both-locale WotD hub chrome strings", () => {
    for (const key of [
      "wotd.subtitle",
      "wotd.practiceCta",
      "wotd.todayTitle",
      "wotd.todayDescription",
      "wotd.loading",
      "wotd.loadError",
    ] as const) {
      expect(CHROME_STRINGS.en[key].length).toBeGreaterThan(0);
      expect(CHROME_STRINGS.uk[key].length).toBeGreaterThan(0);
      expect(CHROME_STRINGS.en[key]).not.toEqual(CHROME_STRINGS.uk[key]);
    }
    expect(chromeDict).toContain("'wotd.todayTitle'");
  });

  test("pluralized level count line dual-renders in both locales (DOM)", () => {
    const { en, uk } = formatWotdLevelCount("A2", 12);
    expect(en).toBe("A2 · 12 words");
    expect(uk).toBe("A2 · 12 слів");

    const one = formatWotdLevelCount("A1", 1);
    expect(one.en).toBe("A1 · 1 word");
    expect(one.uk).toBe("A1 · 1 слово");

    const few = formatWotdLevelCount("B1", 3);
    expect(few.en).toBe("B1 · 3 words");
    expect(few.uk).toBe("B1 · 3 слова");

    document.body.innerHTML = chromeDualHtml(en, uk);
    const rootEl = document.querySelector(".lu-i18n")!;
    expect(rootEl.querySelector('[data-loc="en"]')?.textContent).toBe(en);
    expect(rootEl.querySelector('[data-loc="uk"]')?.textContent).toBe(uk);

    // CSS show/hide contract: English visible by default; UK when attribute set.
    document.documentElement.dataset.chromeLocale = "en";
    expect(rootEl.querySelector('[data-loc="en"]')).toBeTruthy();
    document.documentElement.dataset.chromeLocale = "uk";
    expect(rootEl.querySelector('[data-loc="uk"]')?.textContent).toContain("слів");
  });

  test("empty-level status is bilingual chrome, not Ukrainian-only", () => {
    const empty = formatWotdEmptyLevel("C2");
    expect(empty.en).toContain("C2");
    expect(empty.en.toLowerCase()).toContain("no words");
    expect(empty.uk).toContain("C2");
    expect(empty.uk).toContain("Немає слів");
  });

  test("DailyWords client status uses chromeDualHtml / formatWotdLevelCount", () => {
    expect(dailyWords).toContain("chromeDualHtml");
    expect(dailyWords).toContain("formatWotdLevelCount");
    expect(dailyWords).toContain("formatWotdEmptyLevel");
  });
});
