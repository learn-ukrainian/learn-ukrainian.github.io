import { describe, expect, test } from "vitest";
import { withholdLegacySovietCitations } from "@site/src/lib/lexicon/soviet-citation-withholding";

describe("legacy Soviet citation withholding", () => {
  test.each([
    ["абрикос", "synonyms", "Словник синонімів + СУМ-20: Те саме, що → абрикоса + ВТС: → абрикоса + СУМ-11: → абрикоса", ["абрикоса", "жерделя", "мореля"], ["абрикоса", "жерделя", "мореля"]],
    ["латиниця", "synonyms", "СУМ-20: → латинка + СУМ-11: → латинка + СУМ-11: → абетка", ["латинка", "абетка"], ["латинка"]],
    ["розширити", "antonyms", "ВТС: протилежне → звузити + СУМ-11: → скоротити", ["звузити", "скоротити"], ["звузити"]],
    ["відбігти", "synonyms", "СУМ-20: → віддалитися + СУМ-11: → відскочити", ["віддалитися", "відскочити"], ["віддалитися"]],
  ] as const)("keeps only supported items for %s", (lemma, section, source, items, expected) => {
    const entry = { lemma, sections: { [section]: { source, items } } };
    const projected = withholdLegacySovietCitations(entry);
    expect(projected.sections[section].items).toEqual(expected);
    expect(projected.sections[section].source).not.toContain("СУМ-11");
    if (expected.length !== items.length) {
      expect(projected).toHaveProperty(`gate_provenance.${section}`, "source-withdrawn-unverified");
    }
  });

  test.each([
    ["ера", "епоха", "СУМ-11/СУМ-11 stem=булий"],
    ["броня", "кольчуга", "СУМ-20/СУМ-11 stem=воїн"],
  ])("strips a gate note but keeps the WordNet item for %s", (lemma, item, gate) => {
    const source = `Ukrajinet WordNet: gated synset → ${item} [gate: VESUM both valid; ${gate}]`;
    const projected = withholdLegacySovietCitations({
      lemma, sections: { synonyms: { items: [item], source } }, enrichment: { sources: [source] },
    });
    const clean = `Ukrajinet WordNet: gated synset → ${item}`;
    expect(projected.sections.synonyms).toEqual({ items: [item], source: clean });
    expect(projected.enrichment.sources).toEqual([clean]);
  });

  test("withholds a sole-source relation and marks it unverified", () => {
    const projected = withholdLegacySovietCitations({
      sections: { synonyms: { items: ["назва"], source: "СУМ-11: → назва" } },
    });
    expect(projected.sections).not.toHaveProperty("synonyms");
    expect(projected).toHaveProperty("gate_provenance.synonyms", "source-withdrawn-unverified");
  });

  test("preserves a corpus quote but withholds the same wording as an attribution", () => {
    const quote = "«Словник української мови» в 11 томах (1970 — 80)";
    const attestation = { text: quote, source: "2004 encyclopedia" };
    expect(withholdLegacySovietCitations({ enrichment: { literary_attestation: attestation } }))
      .toEqual({ enrichment: { literary_attestation: attestation } });
    const projected = withholdLegacySovietCitations({ enrichment: { literary_attestation: {
      ...attestation, source: quote,
    } } });
    expect(projected.enrichment).not.toHaveProperty("literary_attestation");
  });
});
