import { describe, expect, test } from "vitest";
import { cleanOriginText, formatOrigin, formatOriginSource } from "@site/src/lib/lexicon/format-origin";

describe("formatOrigin", () => {
  test("returns null for missing/empty input", () => {
    expect(formatOrigin(undefined)).toBeNull();
    expect(formatOrigin(null)).toBeNull();
    expect(formatOrigin({ text: "", source: "kaikki/Wiktionary (CC BY-SA 3.0)" })).toBeNull();
    expect(formatOrigin({ text: "   ", source: "kaikki/Wiktionary (CC BY-SA 3.0)" })).toBeNull();
  });

  test("strips Latin-script transliteration parentheticals", () => {
    const result = formatOrigin({
      text: "From наштовх(ну́ти) (naštovx(núty)) + -увати (-uvaty).",
      source: "kaikki/Wiktionary (CC BY-SA 3.0)",
    });
    expect(result).not.toBeNull();
    expect(result!.text).toBe("From наштовх(ну́ти) + -увати.");
    expect(result!.source).toBe("Wiktionary");
  });

  test("strips English gloss parentheticals", () => {
    const result = formatOrigin({
      text: "Borrowed from French prognose, from Ancient Greek πρόγνωσις (prógnōsis, “foreknowledge, perceiving beforehand, prediction”).",
      source: "kaikki/Wiktionary (CC BY-SA 3.0)",
    });
    expect(result).not.toBeNull();
    expect(result!.text).toBe("Borrowed from French prognose, from Ancient Greek πρόγνωσις.");
  });

  test("removes imperial comparison clauses", () => {
    const result = formatOrigin({
      text: "From одно- + кімна́та + -ний. Compare Russian одноко́мнатный.",
      source: "kaikki/Wiktionary (CC BY-SA 3.0)",
    });
    expect(result).not.toBeNull();
    expect(result!.text).toBe("From одно- + кімна́та + -ний.");
  });

  test("rejects ESUM/mphdict internal labels", () => {
    expect(
      formatOrigin({
        text: "Стаття ЕСУМ: вода; етимонів: 3.",
        source: "ЕСУМ",
      }),
    ).toBeNull();
  });

  test("rejects text that becomes empty after cleaning", () => {
    expect(
      formatOrigin({
        text: "(núty) (odnokómnatnyj)",
        source: "kaikki/Wiktionary (CC BY-SA 3.0)",
      }),
    ).toBeNull();
  });

  test("truncates long cleaned strings cleanly", () => {
    const long = "From Proto-Slavic " + "*example ".repeat(40);
    const result = formatOrigin({ text: long, source: "kaikki/Wiktionary (CC BY-SA 3.0)" });
    expect(result).not.toBeNull();
    expect(result!.text.length).toBeLessThanOrEqual(170);
    expect(result!.text.endsWith("…")).toBe(true);
  });

  test("sentence-cases the result", () => {
    const result = formatOrigin({
      text: "from Latin monēta.",
      source: "kaikki/Wiktionary (CC BY-SA 3.0)",
    });
    expect(result!.text).toBe("From Latin monēta.");
  });

  test("formatOriginSource maps Kaikki source to Wiktionary", () => {
    expect(formatOriginSource("kaikki/Wiktionary (CC BY-SA 3.0)")).toBe("Wiktionary");
  });

  test("formatOriginSource passes through unknown sources", () => {
    expect(formatOriginSource("ЕСУМ")).toBe("ЕСУМ");
    expect(formatOriginSource("")).toBe("");
  });
});

describe("cleanOriginText", () => {
  test("returns null for whitespace or punctuation-only strings", () => {
    expect(cleanOriginText("   ")).toBeNull();
    expect(cleanOriginText("...")).toBeNull();
  });

  test("returns null for missing input", () => {
    expect(cleanOriginText(undefined)).toBeNull();
    expect(cleanOriginText(null)).toBeNull();
  });
});
