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
const courseLayout = readFileSync(resolve(root, "src/layouts/CourseLayout.astro"), "utf8");

/**
 * happy-dom does not recompute attribute-selector CSS when data-chrome-locale
 * flips. Apply the same show/hide contract CourseLayout's .lu-i18n rules define
 * so tests assert actual per-locale visibility, not mere span existence.
 */
function applyLuI18nVisibilityContract(doc: Document = document): void {
  const locale = doc.documentElement.dataset.chromeLocale === "uk" ? "uk" : "en";
  for (const span of doc.querySelectorAll(".lu-i18n [data-loc]")) {
    const el = span as HTMLElement;
    el.style.display = el.getAttribute("data-loc") === locale ? "inline" : "none";
  }
}

function expectOnlyLocaleVisible(rootEl: Element, locale: "en" | "uk"): void {
  applyLuI18nVisibilityContract();
  const en = rootEl.querySelector<HTMLElement>('[data-loc="en"]');
  const uk = rootEl.querySelector<HTMLElement>('[data-loc="uk"]');
  expect(en).toBeTruthy();
  expect(uk).toBeTruthy();
  if (locale === "en") {
    expect(en!.style.display).toBe("inline");
    expect(uk!.style.display).toBe("none");
    expect(getComputedStyle(en!).display).not.toBe("none");
    expect(getComputedStyle(uk!).display).toBe("none");
  } else {
    expect(uk!.style.display).toBe("inline");
    expect(en!.style.display).toBe("none");
    expect(getComputedStyle(uk!).display).not.toBe("none");
    expect(getComputedStyle(en!).display).toBe("none");
  }
}

describe("readings chrome locale (#6750 already on HEAD)", () => {
  test("readings index wires hero + search through Chrome Locale Runtime", () => {
    expect(readingsIndex).toContain('titleKey="nav.readings"');
    expect(readingsIndex).toContain('subtitleKey="readings.subtitle"');
    expect(readingsIndex).toContain("data-i18n-placeholder");
    expect(readingsIndex).toContain("readings.searchPlaceholder");
  });
});

describe("WotD hub chrome locale (#6711)", () => {
  test("document title stays bilingual — titleKey does not drive <title>", () => {
    // CourseLayout titleKey dual-renders hero <h1> only; <title> stays the
    // plain `title` prop (same as readings after #6750). Restore bilingual tab
    // title so УКР mode is not English-only in browser chrome.
    expect(wotdHub).toContain('title: "Слова дня / Words of the Day"');
    expect(courseLayout).toContain("<title>{title} · Learn Ukrainian</title>");
    expect(courseLayout).toMatch(/titleKey\s*\?\s*<ChromeText/);
    expect(courseLayout).not.toMatch(/<title>\{[^}]*titleKey/);
  });

  test("hub hero dual-renders title, subtitle, badge, and practice CTA via ChromeText", () => {
    expect(wotdHub).toContain("ChromeText");
    expect(wotdHub).toMatch(/ChromeText\s+k="nav\.dailyWords"/);
    expect(wotdHub).toMatch(/ChromeText\s+k="wotd\.subtitle"/);
    expect(wotdHub).toMatch(/ChromeText\s+k="wotd\.practiceCta"/);
    // No slash-dual leftovers in visible hero (#5503) and no Ukrainian-only hero chrome.
    expect(wotdHub).not.toMatch(/<h1[^>]*>\s*Слова дня\s*\/\s*Words of the Day/);
    expect(wotdHub).not.toMatch(/<h1[^>]*>\s*Слова дня\s*</);
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

  test("pluralized level count line dual-renders with per-locale visibility", () => {
    const { en, uk } = formatWotdLevelCount("A2", 12);
    expect(en).toBe("A2 · 12 words");
    expect(uk).toBe("A2 · 12 слів");

    const one = formatWotdLevelCount("A1", 1);
    expect(one.en).toBe("A1 · 1 word");
    expect(one.uk).toBe("A1 · 1 слово");

    const few = formatWotdLevelCount("B1", 3);
    expect(few.en).toBe("B1 · 3 words");
    expect(few.uk).toBe("B1 · 3 слова");

    // CourseLayout CSS contract must still hide the inactive locale.
    expect(courseLayout).toContain(".lu-i18n [data-loc='uk'] { display: none; }");
    expect(courseLayout).toContain(
      "html[data-chrome-locale='uk'] .lu-i18n [data-loc='en'] { display: none; }",
    );

    document.body.innerHTML = chromeDualHtml(en, uk);
    const rootEl = document.querySelector(".lu-i18n")!;

    document.documentElement.dataset.chromeLocale = "en";
    expectOnlyLocaleVisible(rootEl, "en");
    expect(rootEl.querySelector('[data-loc="en"]')?.textContent).toBe(en);

    document.documentElement.dataset.chromeLocale = "uk";
    expectOnlyLocaleVisible(rootEl, "uk");
    expect(rootEl.querySelector('[data-loc="uk"]')?.textContent).toContain("слів");
  });

  test("chromeDualHtml escapes angle brackets, ampersand, and quotes", () => {
    const en = `A <b>bold</b> & "quoted" path`;
    const uk = `Шляхх <img src=x onerror=alert(1)> & 'лапк'`;
    const html = chromeDualHtml(en, uk);

    // Assert entities on the fragment string before the DOM re-serializes text nodes.
    expect(html).toContain("&lt;b&gt;");
    expect(html).toContain("&lt;/b&gt;");
    expect(html).toContain("&amp;");
    expect(html).toContain("&quot;quoted&quot;");
    expect(html).toContain("&lt;img src=x onerror=alert(1)&gt;");
    expect(html).not.toMatch(/<b>|<img\b/);

    document.body.innerHTML = html;
    const rootEl = document.querySelector(".lu-i18n")!;

    // No injected element nodes — only the two locale spans under .lu-i18n.
    expect(rootEl.querySelectorAll("*")).toHaveLength(2);
    expect(rootEl.querySelector("b")).toBeNull();
    expect(rootEl.querySelector("img")).toBeNull();
    expect(document.body.querySelectorAll("script")).toHaveLength(0);

    // Exact text preserved after parse.
    expect(rootEl.querySelector('[data-loc="en"]')?.textContent).toBe(en);
    expect(rootEl.querySelector('[data-loc="uk"]')?.textContent).toBe(uk);
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
    expect(dailyWords).toContain("applyDailyLoadFallback");
    expect(dailyWords).toContain("beginDailyReload");
    expect(dailyWords).toContain("markDailyLoadSuccess");
  });
});
