import { describe, expect, test } from "vitest";
import { formatOrigin } from "@site/src/lib/lexicon/format-origin";
import {
  atlasWikipediaOkAsIntro,
  buildAtlasLinkCatalogFromSearchRows,
  buildWordAtlasArticleView,
  formatPos,
  formatTranslationSource,
  sanitizeWikiReference,
  type AtlasLinkCatalog,
  type Enrichment,
  type VerbParadigm,
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

  test("overview origin card waits for a source when origin is missing", () => {
    const view = buildWordAtlasArticleView(makeEntry().record, "test", "test");
    const originCard = view.articleOverview.find((card) => card.label === "Походження");
    expect(originCard).toBeDefined();
    expect(originCard!.ready).toBe(false);
    expect(originCard!.detail).toBe("очікує джерело");
  });

  test("overview origin card uses a short count instead of formatted prose", () => {
    const view = buildWordAtlasArticleView(
      makeEntry({ text: "From Latin monēta.", source: "kaikki/Wiktionary (CC BY-SA 3.0)" }).record,
      "test",
      "test",
    );
    const originCard = view.articleOverview.find((card) => card.label === "Походження");
    expect(originCard).toBeDefined();
    expect(originCard!.ready).toBe(true);
    expect(originCard!.detail).toBe("1 картка");
  });

  test("overview origin card does not expose an ESUM-style dump", () => {
    const dump = "Вода, віднйк «діжечка для води»…";
    const view = buildWordAtlasArticleView(
      makeEntry({ text: dump, source: "ЕСУМ" }).record,
      "test",
      "test",
    );
    const originCard = view.articleOverview.find((card) => card.label === "Походження");
    expect(originCard).toBeDefined();
    expect(originCard!.ready).toBe(true);
    expect(originCard!.detail).toBe("1 картка");
    expect(originCard!.detail).not.toContain(dump);
  });

  test("article etymology renders full stored ESUM text, not a 160-char clip", () => {
    // Long enough that formatOrigin would truncate with "…" — article must keep the store.
    const fullEsum =
      "псл. *voda; споріднене з лит. vanduõ, vandеñs «вода», прус. wundan, гот. watō, двн. waʒӡаr «тс.», " +
      "інд. udakám «вода», тох. А/В wär «тс.»; іє. *u̯ed- / *u̯od- «мокрий, вода»; " +
      "пор. також дінд. unátti «змочує», лат. unda «хвиля».";
    expect(fullEsum.length).toBeGreaterThan(160);
    const clipped = formatOrigin({ text: fullEsum, source: "ЕСУМ, т. 1, с. 413" });
    expect(clipped?.text.endsWith("…")).toBe(true);
    expect(clipped!.text).not.toBe(fullEsum);

    const html = renderWordAtlasArticle(
      articleProps({
        lemma: "вода",
        url_slug: "вода",
        gloss: "water",
        entry_type: "lemma",
        pos: "noun",
        ipa: null,
        primary_source: "course",
        course_usage: [],
        enrichment: {
          etymology: { text: fullEsum, source: "ЕСУМ, т. 1, с. 413" },
        },
      }),
    );
    expect(html).toContain(fullEsum);
    expect(html).toContain("Джерело: ЕСУМ, т. 1, с. 413");
    expect(html).not.toContain(clipped!.text);
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
          sources: ["learner_english_gloss"],
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
    expect(view.sourceList).not.toContain("learner_english_gloss");
    expect(view.sourceList.filter((source) => source === "Anna Ohoiko")).toHaveLength(1);
  });
});

describe("translation source humanization (#7459)", () => {
  test("maps learner_english_gloss to Anna Ohoiko", () => {
    expect(formatTranslationSource("learner_english_gloss")).toBe("Anna Ohoiko");
  });

  test("maps agy_en_proposal to the model translation label", () => {
    expect(formatTranslationSource("agy_en_proposal")).toBe("модельний переклад");
  });

  test("keeps dmklinger and other sources distinct", () => {
    expect(formatTranslationSource("dmklinger")).toBe("dmklinger");
    expect(formatTranslationSource("Wikidata")).toBe("Wikidata");
    expect(formatTranslationSource("kaikki")).toBe("kaikki");
  });

  test("handles nullish translation sources", () => {
    expect(formatTranslationSource(undefined)).toBeNull();
    expect(formatTranslationSource(null)).toBeNull();
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

describe("verb pedagogy strip (#7471)", () => {
  function verbProps(verb_pedagogy: Enrichment["verb_pedagogy"]) {
    return articleProps({
      lemma: "аналізувати",
      url_slug: "аналізувати",
      gloss: "to analyze",
      entry_type: "lemma",
      pos: "verb",
      ipa: null,
      primary_source: "course",
      course_usage: [],
      enrichment: { verb_pedagogy },
    });
  }

  test("renders aspect, partner link, stems, and government when all present", () => {
    const html = renderWordAtlasArticle(
      verbProps({
        aspect: "imperfective",
        aspect_partner: { lemma: "проаналізувати", url_slug: "проаналізувати", source: "Anna Ohoiko" },
        stems: { present_future: ["аналізу-", "проаналізу-"], source: "Anna Ohoiko" },
        government: [{ label: "+ accusative", source: "Anna Ohoiko" }],
      }),
    );
    expect(html).toContain("<h2>Вид і керування</h2>");
    expect(html).toContain("недоконаний");
    expect(html).toContain('href="/lexicon/проаналізувати"');
    expect(html).toContain("проаналізувати");
    expect(html).toContain("аналізу- | проаналізу-");
    expect(html).toContain("+ accusative");
    expect(html).toContain("Джерело: VESUM, Anna Ohoiko");
  });

  test("renders a plain partner label without a link when url_slug is absent", () => {
    const html = renderWordAtlasArticle(
      verbProps({ aspect_partner: { lemma: "проаналізувати", source: "Anna Ohoiko" } }),
    );
    expect(html).toContain("проаналізувати");
    expect(html).not.toContain('href="/lexicon/проаналізувати"');
  });

  test("omits the whole section when verb_pedagogy is absent", () => {
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
      }),
    );
    expect(html).not.toContain("Вид і керування");
  });

  test("omits the section when verb_pedagogy is present but empty", () => {
    const html = renderWordAtlasArticle(verbProps({}));
    expect(html).not.toContain("Вид і керування");
  });
});

describe("verb imperative and past morphology blocks (#7609)", () => {
  function verbProps(
    paradigm?: VerbParadigm,
    forms: Array<{ form: string; label: string }> = [],
    lemma = "бути",
  ) {
    return articleProps({
      lemma,
      url_slug: lemma,
      gloss: lemma === "читати" ? "to read" : "to be",
      entry_type: "lemma",
      pos: "verb",
      ipa: null,
      primary_source: "course",
      course_usage: [],
      enrichment: {
        morphology: {
          pos: "verb",
          form_count: forms.length,
          forms,
          source: "VESUM",
          paradigm,
        },
      },
    });
  }

  test("renders imperative and past forms in their own tables", () => {
    const html = renderWordAtlasArticle(
      verbProps({
        kind: "verb",
        infinitive: "бути",
        tenses: {
          теперішній: { однина: { "1": "є" }, множина: { "1": "є" } },
        },
        imperative: { однина: { "2": "будь" }, множина: { "1": "будьмо", "2": "будьте" } },
        past: { "чол.": "був", "жін.": "була", "сер.": "було", множина: "були" },
      }),
    );

    const document = new DOMParser().parseFromString(html, "text/html");
    const tableWithCaption = (caption: string) =>
      Array.from(document.querySelectorAll("table")).find(
        (table) => table.querySelector("caption")?.textContent === caption,
      );
    const tableRows = (caption: string) => {
      const table = tableWithCaption(caption);
      expect(table).toBeDefined();
      return Array.from(table!.querySelectorAll("tbody tr")).map((row) =>
        Array.from(row.querySelectorAll("td")).map((cell) => cell.textContent),
      );
    };

    expect(tableRows("Наказовий")).toEqual([
      ["2 особа", "будь", ""],
      ["1 особа (мн.)", "", "будьмо"],
      ["2 особа (мн.)", "", "будьте"],
    ]);
    expect(tableRows("Минулий")).toEqual([
      ["чол.", "був"],
      ["жін.", "була"],
      ["сер.", "було"],
      ["множина", "були"],
    ]);
  });

  test("does not render imperative or past captions for a tense-only paradigm", () => {
    const html = renderWordAtlasArticle(
      verbProps({
        kind: "verb",
        tenses: {
          теперішній: { однина: { "1": "є" } },
          майбутній: {},
        },
      }),
    );

    expect(html).toContain("<caption>теперішній</caption>");
    expect(html).not.toContain("майбутній");
    expect(html).not.toContain("Наказовий");
    expect(html).not.toContain("Минулий");
  });

  test("does not render empty imperative or past sub-blocks", () => {
    const html = renderWordAtlasArticle(
      verbProps({
        kind: "verb",
        imperative: { однина: { "2": "" }, множина: {} },
        past: { "чол.": "", "жін.": "", "сер.": "", множина: "" },
      }),
    );

    expect(html).not.toContain("Наказовий");
    expect(html).not.toContain("Минулий");
  });

  test("keeps an unstructured empty-label verb on the fallback path", () => {
    const html = renderWordAtlasArticle(
      verbProps(undefined, [{ form: "читати", label: "" }], "читати"),
    );

    expect(html).toContain("читати");
    expect(html).not.toContain("Наказовий");
    expect(html).not.toContain("Минулий");
  });
});

describe("Atlas lexical backlinks (#7610)", () => {
  type FixtureEntry = Parameters<typeof articleProps>[0];
  type CatalogEntry = AtlasLinkCatalog["entries"][number];

  function fixtureEntry(lemma: string, overrides: Record<string, unknown> = {}): FixtureEntry {
    return {
      lemma,
      url_slug: lemma,
      gloss: null,
      entry_type: "lemma",
      pos: "noun",
      ipa: null,
      primary_source: "fixture",
      course_usage: [],
      ...overrides,
    } as FixtureEntry;
  }

  function catalogEntry(
    lemma: string,
    overrides: Partial<CatalogEntry> = {},
  ): CatalogEntry {
    return { lemma, slug: lemma, entry_type: "lemma", ...overrides };
  }

  test("links canonical synonym, antonym, alias, and paronym targets while failing closed", () => {
    const catalog: AtlasLinkCatalog = {
      entries: [
        catalogEntry("читати", { pos: "infinitive" }),
        catalogEntry("ректи", { pos: "infinitive" }),
        catalogEntry("протилежний"),
        catalogEntry("двозначний", { slug: "двозначний-1", pos: "noun" }),
        catalogEntry("двозначний", { slug: "двозначний-2", pos: "verb" }),
        catalogEntry("змішаний", { pos: "іменник або дієслово" }),
      ],
      aliases: [{ alias: "говорити", target_slug: "ректи" }],
    };
    const entry = fixtureEntry("читати", {
      pos: "verb",
      sections: {
        synonyms: { items: ["ректи (заст.)", "говорити", "відсутній", "двозначний", "змішаний"], source: "fixture" },
        antonyms: { items: ["протилежний"], source: "fixture" },
        paronyms: { items: [{ word: "ректи (заст.)", distinction: "інше значення" }], source: "fixture" },
      },
    });
    const html = renderWordAtlasArticle({
      ...articleProps(entry),
      atlasLinkCatalog: catalog,
    });

    expect(html).toContain('href="/lexicon/ректи"');
    expect(html).toContain('>ректи (заст.)</a>');
    expect(html).toContain('>говорити</a>');
    expect(html).toContain('href="/lexicon/протилежний"');
    expect(html).toContain("Не плутати з");
    expect(html).not.toContain('href="/lexicon/відсутній"');
    expect(html).not.toContain('href="/lexicon/двозначний-1"');
    expect(html).not.toContain('href="/lexicon/змішаний"');
    expect(html).not.toContain('href="/lexicon/читати"');
  });

  test("uses a verified relation target even when the in-memory catalog omits its article", () => {
    const entry = fixtureEntry("джерело", {
      sections: { synonyms: { items: ["ректи (заст.)"], source: "fixture" } },
    });
    const props = articleProps(entry);
    const record = {
      ...props.record,
      relations: [
        {
          related_slug: "ректи",
          entry_type: null,
          relation: "synonym",
          component_role: null,
          provenance: "verified",
        },
      ],
    };
    const html = renderWordAtlasArticle({
      ...props,
      record,
      atlasLinkCatalog: { entries: [catalogEntry("джерело")] },
    });

    expect(html).toContain('href="/lexicon/ректи"');
    expect(html).toContain('>ректи (заст.)</a>');
  });

  test("links passive participle parents and lists only passive participles on the verb", () => {
    const passiveParadigm = {
      kind: "participle" as const,
      voice: "passive" as const,
      aspect: "imperfective" as const,
      verb: "читати",
    };
    const activeParadigm = {
      kind: "participle" as const,
      voice: "active" as const,
      aspect: "imperfective" as const,
      verb: "читати",
    };
    const morphology = (paradigm: typeof passiveParadigm | typeof activeParadigm) => ({
      pos: "прикметник",
      form_count: 1,
      forms: [{ form: "форма", label: "називний" }],
      source: "VESUM",
      paradigm,
    });
    const catalog: AtlasLinkCatalog = {
      entries: [
        catalogEntry("читати", { pos: "infinitive" }),
        catalogEntry("читаний", { pos: "adjective", enrichment: { morphology: morphology(passiveParadigm) } }),
        catalogEntry("активний", { pos: "adjective", enrichment: { morphology: morphology(activeParadigm) } }),
        catalogEntry("читаючи", { pos: "adverb", gloss: "Дієприсл. доконаного виду до читати." }),
      ],
    };

    const participleHtml = renderWordAtlasArticle({
      ...articleProps(fixtureEntry("читаний", {
        pos: "adjective",
        enrichment: { morphology: morphology(passiveParadigm) },
      })),
      atlasLinkCatalog: catalog,
    });
    const verbHtml = renderWordAtlasArticle({
      ...articleProps(fixtureEntry("читати", { pos: "verb" })),
      atlasLinkCatalog: catalog,
    });

    expect(participleHtml).toContain('href="/lexicon/читати"');
    expect(verbHtml).toContain("<h2>Дієприкметники</h2>");
    expect(verbHtml).toContain('href="/lexicon/читаний"');
    expect(verbHtml).toContain("дієприкметник");
    expect(verbHtml).not.toContain('href="/lexicon/активний"');
    expect(verbHtml).not.toContain('href="/lexicon/читаючи"');
  });

  test("derives passive relationships from search-index glosses without treating gerund glosses as parent evidence", () => {
    const catalog = buildAtlasLinkCatalogFromSearchRows([
      { l: "читати", s: "читати", g: "to read", t: "lemma" },
      { l: "читаний", s: "читаний", g: "Дієпр. пас. мин. і теп. ч. до чита́ти.", t: "lemma" },
      { l: "читаючи", s: "читаючи", g: "Дієприсл. недоконаного виду до читати.", t: "lemma" },
    ]);
    const view = buildWordAtlasArticleView(
      articleProps(fixtureEntry("читати", { pos: "verb" })).record,
      "test",
      "test",
      catalog,
    );

    expect(view.participleLinks).toEqual([{ lemma: "читаний", slug: "читаний" }]);
    expect(view.gerundLinks).toEqual([]);
  });

  test("lists producer-verified gerunds on their verb page", () => {
    const catalog = buildAtlasLinkCatalogFromSearchRows([
      { l: "читати", s: "читати", g: "to read", t: "lemma" },
      {
        l: "читаючи",
        s: "читаючи",
        g: "while reading",
        t: "lemma",
        p: "чита́ти",
      },
    ]);
    const props = articleProps(fixtureEntry("читати", { pos: "verb" }));
    const view = buildWordAtlasArticleView(props.record, "test", "test", catalog);
    const html = renderWordAtlasArticle({ ...props, atlasLinkCatalog: catalog });

    expect(view.gerundLinks).toEqual([{ lemma: "читаючи", slug: "читаючи" }]);
    expect(html).toContain("<h2>Дієприслівники</h2>");
    expect(html).toContain('href="/lexicon/читаючи"');
    expect(html).toContain("дієприслівник");
  });

  test("fails closed for parentless, unresolved, and ambiguous gerund parents", () => {
    const catalog = buildAtlasLinkCatalogFromSearchRows([
      { l: "читати", s: "читати", g: "to read", t: "lemma" },
      { l: "читаючи", s: "читаючи", g: "while reading", t: "lemma", p: "читати" },
      { l: "зробивши", s: "зробивши", g: "having done", t: "lemma", p: "відсутній" },
      {
        l: "сидячи",
        s: "сидячи",
        g: "Дієприсл. недоконаного виду до сидіти.",
        t: "lemma",
      },
    ]);
    const props = articleProps(fixtureEntry("читати", { pos: "verb" }));
    const html = renderWordAtlasArticle({ ...props, atlasLinkCatalog: catalog });

    expect(html).toContain('href="/lexicon/читаючи"');
    expect(html).not.toContain('href="/lexicon/зробивши"');
    expect(html).not.toContain('href="/lexicon/сидячи"');

    const ambiguousCatalog = buildAtlasLinkCatalogFromSearchRows([
      { l: "читати", s: "читати-1", g: "to read", t: "lemma" },
      { l: "читати", s: "читати-2", g: "to read", t: "lemma" },
      { l: "читаючи", s: "читаючи", g: "while reading", t: "lemma", p: "читати" },
    ]);
    const ambiguousProps = articleProps(
      fixtureEntry("читати", { url_slug: "читати-1", pos: "verb" }),
    );
    const ambiguousView = buildWordAtlasArticleView(
      ambiguousProps.record,
      "test",
      "test",
      ambiguousCatalog,
    );

    expect(ambiguousView.gerundLinks).toEqual([]);
  });
});
