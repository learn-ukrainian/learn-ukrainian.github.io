import { describe, expect, test } from "vitest";
import { buildWordAtlasArticleView, formatPos } from "@site/src/lib/lexicon/word-atlas-article-model";
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
