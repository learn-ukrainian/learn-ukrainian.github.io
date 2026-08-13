// @vitest-environment happy-dom

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, test } from "vitest";
import { GET as getDailyPool } from "@site/src/pages/api/lexicon/daily-pool.json";
import type { DailyWord } from "@site/src/lib/lexicon/daily";
import {
  bindDailyCardInteractions,
  dailyCardAtlasHref,
  isDailyCardAtlasLinkTarget,
  renderDailyCardHtml,
  toggleDailyCardFlip,
} from "@site/src/lib/lexicon/daily-card";

const dailyWordsSource = readFileSync(
  resolve(process.cwd(), "src/lexicon/DailyWords.astro"),
  "utf8",
);
const wordsOfTheDaySource = readFileSync(
  resolve(process.cwd(), "src/pages/words-of-the-day.astro"),
  "utf8",
);

const sampleWord: DailyWord = {
  lemma: "кошик",
  slug: "кошик",
  gloss: "basket",
  cefr: "A1",
  example: "У кошику яблука.",
  exampleEn: "There are apples in the basket.",
};

describe("DailyWords list example sentence (GH #5434)", () => {
  test("DailyWords Astro renders an example slot with bilingual scaffolding", () => {
    expect(dailyWordsSource).toContain("renderDailyCardHtml");
    const html = renderDailyCardHtml(sampleWord);
    expect(html).toContain('data-testid="daily-example-кошик"');
    expect(html).toContain('class="lexicon-daily-example"');
    expect(html).toContain('class="lexicon-daily-example-en"');
    expect(html).toContain('lang="uk"');
    expect(html).toContain('lang="en"');
  });

  test("DailyWords card omits example markup when no example is present", () => {
    const html = renderDailyCardHtml({
      lemma: "хліб",
      slug: "хліб",
      gloss: "bread",
    });
    expect(html).not.toContain("lexicon-daily-example");
  });

  test("daily pool API route exposes optional example fields", async () => {
    const response = await getDailyPool({} as Parameters<typeof getDailyPool>[0]);
    const pool = (await response.json()) as DailyWord[];

    expect(Array.isArray(pool)).toBe(true);
    expect(pool.length).toBeGreaterThan(0);

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

describe("DailyWords card flip vs Atlas lemma (#6726)", () => {
  test("hub copy no longer claims every card goes to Atlas", () => {
    expect(wordsOfTheDaySource).not.toContain("кожна картка веде до повної статті Атласу");
    expect(wordsOfTheDaySource).toContain("торкніться картки, щоб перевернути");
    expect(wordsOfTheDaySource).toContain("Атласі");
  });

  test("card chrome is a flip control, not a single Atlas anchor", () => {
    const html = renderDailyCardHtml(sampleWord);
    expect(html).not.toMatch(/<a class="lexicon-daily-card"/);
    expect(html).toContain('data-daily-card');
    expect(html).toContain('data-flipped="false"');
    expect(html).toContain('role="button"');
    expect(html).toContain("lexicon-daily-front");
    expect(html).toContain("lexicon-daily-back");
  });

  test("lemma text is the Atlas link; gloss lives on the back face", () => {
    document.body.innerHTML = renderDailyCardHtml(sampleWord);
    const lemma = document.querySelector<HTMLAnchorElement>("[data-daily-atlas-link]")!;
    const front = document.querySelector(".lexicon-daily-front")!;
    const back = document.querySelector(".lexicon-daily-back")!;

    expect(lemma.href).toContain(dailyCardAtlasHref("кошик"));
    expect(lemma.textContent).toBe("кошик");
    expect(front.querySelector(".lexicon-daily-gloss")).toBeNull();
    expect(back.querySelector(".lexicon-daily-gloss")?.textContent).toBe("basket");
    expect(front.querySelector(".lexicon-daily-flip-hint")).not.toBeNull();
  });

  test("lemma without Atlas entry is plain text, not a link", () => {
    const html = renderDailyCardHtml({
      ...sampleWord,
      hasAtlasEntry: false,
    });
    expect(html).toContain('<span class="lexicon-daily-lemma">кошик</span>');
    expect(html).not.toContain("data-daily-atlas-link");
  });

  test("chrome click flips; lemma click target is ignored for flip", () => {
    document.body.innerHTML = `<ul>${renderDailyCardHtml(sampleWord)}</ul>`;
    const list = document.querySelector("ul")!;
    bindDailyCardInteractions(list);

    const card = list.querySelector<HTMLElement>("[data-daily-card]")!;
    const lemma = list.querySelector<HTMLAnchorElement>("[data-daily-atlas-link]")!;
    const gloss = list.querySelector(".lexicon-daily-gloss")!;

    expect(card).toHaveAttribute("data-flipped", "false");
    expect(isDailyCardAtlasLinkTarget(lemma)).toBe(true);
    expect(isDailyCardAtlasLinkTarget(gloss)).toBe(false);

    gloss.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(card).toHaveAttribute("data-flipped", "true");
    expect(card).toHaveAttribute("aria-pressed", "true");

    lemma.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(card).toHaveAttribute("data-flipped", "true");

    toggleDailyCardFlip(card);
    expect(card).toHaveAttribute("data-flipped", "false");
  });

  test("DailyWords wires the shared card helpers", () => {
    expect(dailyWordsSource).toContain('from "../lib/lexicon/daily-card"');
    expect(dailyWordsSource).toContain("bindDailyCardInteractions");
    expect(dailyWordsSource).toContain("renderDailyCardHtml");
  });
});
