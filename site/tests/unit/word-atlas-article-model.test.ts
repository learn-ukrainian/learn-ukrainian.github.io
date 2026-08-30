import { describe, expect, test } from "vitest";
import {
  atlasWikipediaOkAsIntro,
  buildWordAtlasArticleView,
  formatPos,
  formatTranslationSource,
  humanizeTranslationSource,
  sanitizeWikiReference,
} from "@site/src/lib/lexicon/word-atlas-article-model";
import { renderWordAtlasArticle } from "../helpers/render-word-atlas-article";
import { articleProps } from "../helpers/word-atlas-record";

describe("formatPos", () => {
  test("shows distinct morphology and article readings in stable order", () => {
    expect(formatPos("conjunction", "adverb")).toBe("прислівник · сполучник");
  });

  test("includes later enrichment readings without duplicating labels", () => {
    expect(
      formatPos("conjunction", "adverb", {
        cefrPos: "adverb",
        translationPos: "conjunction",
        definitionCards: [
          {
            id: "vts",
            source: "ВТС",
            definitions: ["1. спол. для протиставлення; 2. присл., у знач. вставн. сл."],
          },
        ],
      }),
    ).toBe("прислівник · сполучник");
  });

  test("tokenizes explicit multi-label signals", () => {
    expect(formatPos("adverb / conjunction", undefined)).toBe("прислівник · сполучник");
  });

  test("does not treat a free-text definition mention as a POS reading", () => {
    expect(
      formatPos("adjective", "adjective", {
        definitionCards: [
          {
            id: "vts",
            source: "ВТС",
            definitions: ["Уживається з іменником у словосполученні."],
          },
        ],
      }),
    ).toBe("прикметник");
  });

  test("keeps a single-POS label when all signals agree", () => {
    expect(formatPos("noun", "noun")).toBe("іменник");
  });
});

describe("formattedOrigin in article view model", () => {
  function makeEntry(etymology?: { text: string; source: string }) {
    return articleProps({
      lemma: "монета",
      url_slug: "moneta",
      gloss: "coin",
      entry_type: "lemma",
      pos: "noun",
      ipa: null,
      primary_source: "course",
      course_usage: [],
      enrichment: etymology ? { etymology } : undefined,
    });
  }

  test("returns cleaned origin for Kaikki-sourced etymology", () => {
    const view = buildWordAtlasArticleView(
      makeEntry({ text: "From Latin monēta.", source: "kaikki/Wiktionary (CC BY-SA 3.0)" }).record,
      "test",
      "test",
    );
    expect(view.formattedOrigin).toEqual({ text: "From Latin monēta.", source: "Wiktionary" });
  });

  test("returns null for ESUM-only label etymology", () => {
    const view = buildWordAtlasArticleView(
      makeEntry({ text: "Стаття ЕСУМ: монета; етимонів: 2.", source: "ЕСУМ" }).record,
      "test",
      "test",
    );
    expect(view.formattedOrigin).toBeNull();
  });

  test("overview origin card reflects formatted origin", () => {
    const view = buildWordAtlasArticleView(
      makeEntry({ text: "From Latin monēta.", source: "kaikki/Wiktionary (CC BY-SA 3.0)" }).record,
      "test",
      "test",
    );
    const originCard = view.articleOverview.find((card) => card.label === "Походження");
    expect(originCard).toBeDefined();
    expect(originCard!.ready).toBe(true);
    expect(originCard!.detail).toBe("From Latin monēta.");
  });
});

describe("Atlas Wikipedia rusalka-kin intro gate (#7379)", () => {
  const liveExtract =
    "Береги́ня — істота східнослов’янської міфології, нижчий дух, споріднений із русалками. Ім'я духа пов'язують з берегами.";
  const goddessExtract =
    "Берегиня — за давньослов'янськими релігійними уявленнями, мати всього живого, первісне божество – захисниця людини.";

  test("refuses the live Берегиня rusalka-kin REST extract", () => {
    expect(
      atlasWikipediaOkAsIntro("берегиня", {
        description: "істота слов'янської міфології",
        extract: liveExtract,
      }),
    ).toBe(false);
    const sanitized = sanitizeWikiReference("берегиня", {
      wikipedia: {
        title: "Берегиня",
        summary: liveExtract,
        url: "https://uk.wikipedia.org/wiki/%D0%91%D0%B5%D1%80%D0%B5%D0%B3%D0%B8%D0%BD%D1%8F",
      },
      wiktionary_url: "https://uk.wiktionary.org/wiki/берегиня",
      attribution: "CC BY-SA 4.0",
    });
    expect(sanitized?.wikipedia).toBeUndefined();
    expect(sanitized?.wiktionary_url).toContain("wiktionary");
  });

  test("hydrated берегиня page keeps СУМ-20 lead and drops Wikipedia rusalka intro", () => {
    const html = renderWordAtlasArticle(
      articleProps({
        lemma: "берегиня",
        url_slug: "берегиня",
        gloss:
          "За давньослов'янськими релігійними уявленнями, мати всього живого, первісне божество – захисниця людини, богиня родючості, природи та добра.",
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
        enrichment: {
          definition_cards: [
            {
              id: "sum20",
              source: "СУМ-20",
              source_pill: "СУМ-20",
              definitions: [
                "1. За давньослов'янськими релігійними уявленнями, мати всього живого, первісне божество – захисниця людини, богиня родючості. 3. заст. Русалка.",
              ],
            },
          ],
          translation: { en: ["Berehynia"], source: "Wikidata" },
        },
        wiki_reference: {
          wikipedia: {
            title: "Берегиня",
            summary: liveExtract,
            url: "https://uk.wikipedia.org/wiki/%D0%91%D0%B5%D1%80%D0%B5%D0%B3%D0%B8%D0%BD%D1%8F",
          },
          wiktionary_url: "https://uk.wiktionary.org/wiki/берегиня",
          attribution: "CC BY-SA 4.0",
        },
      }),
    );
    expect(html).toContain("богиня родючості");
    expect(html).toContain("Berehynia");
    expect(html).toContain("заст. Русалка");
    expect(html).not.toContain("нижчий дух");
    expect(html).not.toContain("споріднений із русалками");
    expect(html).not.toContain("істота східнослов");
  });

  test("keeps a goddess-protectress excerpt and a rusalka lemma card", () => {
    expect(atlasWikipediaOkAsIntro("берегиня", { extract: goddessExtract })).toBe(true);
    expect(
      atlasWikipediaOkAsIntro("русалка", {
        extract: "Русалка — міфологічна істота, нижчий дух, споріднений із русалками.",
      }),
    ).toBe(true);

    const view = buildWordAtlasArticleView(
      articleProps({
        lemma: "берегиня",
        url_slug: "берегиня",
        gloss: goddessExtract,
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
        wiki_reference: {
          wikipedia: {
            title: "Берегиня",
            summary: goddessExtract,
            url: "https://uk.wikipedia.org/wiki/%D0%91%D0%B5%D1%80%D0%B5%D0%B3%D0%B8%D0%BD%D1%8F",
          },
          attribution: "CC BY-SA 4.0",
        },
      }).record,
      "test",
      "test",
    );
    expect(view.entry.wiki_reference?.wikipedia?.summary).toBe(goddessExtract);
  });
});

describe("enrichment.examples in article view and rendering (#7452)", () => {
  test("renders bilingual examples on article HTML", () => {
    const html = renderWordAtlasArticle(
      articleProps({
        lemma: "автобус",
        url_slug: "автобус",
        gloss: "bus",
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
        enrichment: {
          translation: { en: ["bus"], source: "learner_english_gloss" },
          examples: [
            {
              uk: "Сашко́ ї́здить в шко́лу авто́бусом.",
              en: "Sashko goes to school by bus.",
              source: "Anna Ohoiko",
              locator: "ohoiko-1000-words entry 3",
            },
          ],
        },
      }),
    );
    expect(html).toContain("Приклади");
    expect(html).toContain("Сашко́ ї́здить в шко́лу авто́бусом.");
    expect(html).toContain("Sashko goes to school by bus.");
    expect(html).toContain("Anna Ohoiko");
    expect(html).toContain("ohoiko-1000-words entry 3");
  });

  test("includes example source in article sources list", () => {
    const view = buildWordAtlasArticleView(
      articleProps({
        lemma: "автобус",
        url_slug: "автобус",
        gloss: "bus",
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
        enrichment: {
          translation: { en: ["bus"], source: "learner_english_gloss" },
          examples: [
            {
              uk: "Сашко́ ї́здить в шко́лу авто́бусом.",
              en: "Sashko goes to school by bus.",
              source: "Anna Ohoiko",
              locator: "ohoiko-1000-words entry 3",
            },
          ],
        },
      }).record,
      "test",
      "test",
    );
    expect(view.sourceList).toContain("Anna Ohoiko");
    expect(view.sourceList).toContain("learner_english_gloss");
  });
});

describe("translation source humanization (#7459)", () => {
  test("maps learner_english_gloss to Anna Ohoiko", () => {
    expect(formatTranslationSource("learner_english_gloss")).toBe("Anna Ohoiko");
    expect(humanizeTranslationSource("learner_english_gloss")).toBe("Anna Ohoiko");
  });

  test("keeps dmklinger and other sources distinct", () => {
    expect(formatTranslationSource("dmklinger")).toBe("dmklinger");
    expect(humanizeTranslationSource("dmklinger")).toBe("dmklinger");
    expect(formatTranslationSource("Wikidata")).toBe("Wikidata");
    expect(formatTranslationSource("kaikki")).toBe("kaikki");
  });

  test("handles nullish translation sources", () => {
    expect(formatTranslationSource(undefined)).toBeNull();
    expect(formatTranslationSource(null)).toBeNull();
    expect(humanizeTranslationSource(undefined)).toBeNull();
  });

  test("buildWordAtlasArticleView exposes humanized translationSource", () => {
    const ohoikoView = buildWordAtlasArticleView(
      articleProps({
        lemma: "автобус",
        url_slug: "автобус",
        gloss: "bus",
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
        enrichment: {
          translation: { en: ["bus"], source: "learner_english_gloss" },
        },
      }).record,
      "test",
      "test",
    );
    expect(ohoikoView.translationSource).toBe("Anna Ohoiko");

    const dmklingerView = buildWordAtlasArticleView(
      articleProps({
        lemma: "прапор",
        url_slug: "прапор",
        gloss: "flag",
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
        enrichment: {
          translation: { en: ["flag"], source: "dmklinger" },
        },
      }).record,
      "test",
      "test",
    );
    expect(dmklingerView.translationSource).toBe("dmklinger");

    const emptyView = buildWordAtlasArticleView(
      articleProps({
        lemma: "слово",
        url_slug: "слово",
        gloss: "word",
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
      }).record,
      "test",
      "test",
    );
    expect(emptyView.translationSource).toBeNull();
  });

  test("renders Anna Ohoiko label on Переклад block for learner_english_gloss", () => {
    const html = renderWordAtlasArticle(
      articleProps({
        lemma: "автобус",
        url_slug: "автобус",
        gloss: "bus",
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
        enrichment: {
          translation: { en: ["bus"], source: "learner_english_gloss" },
        },
      }),
    );
    expect(html).toContain("<h2>Переклад</h2>");
    expect(html).toContain("Джерело: Anna Ohoiko");
    expect(html).not.toContain("Джерело: learner_english_gloss");
  });

  test("renders dmklinger label on Переклад block for dmklinger", () => {
    const html = renderWordAtlasArticle(
      articleProps({
        lemma: "прапор",
        url_slug: "прапор",
        gloss: "flag",
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
        enrichment: {
          translation: { en: ["flag", "banner"], source: "dmklinger" },
        },
      }),
    );
    expect(html).toContain("<h2>Переклад</h2>");
    expect(html).toContain("Джерело: dmklinger");
    expect(html).not.toContain("Джерело: Anna Ohoiko");
  });
});


