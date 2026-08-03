import { describe, expect, test } from "vitest";
import { formatPos } from "@site/src/lib/lexicon/word-atlas-article-model";

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
