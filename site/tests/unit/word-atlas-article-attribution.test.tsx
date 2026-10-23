import { describe, expect, test } from "vitest";
import type { Enrichment } from "@site/src/lib/lexicon/word-atlas-article-model";
import { renderWordAtlasArticle } from "../helpers/render-word-atlas-article";
import { articleProps } from "../helpers/word-atlas-record";

function render(enrichment: Enrichment): Document {
  return new DOMParser().parseFromString(renderWordAtlasArticle({
    ...articleProps({ lemma: "автобус", url_slug: "автобус", gloss: "bus", pos: "noun",
      entry_type: "lemma", primary_source: "built_vocabulary", course_usage: [], enrichment }),
    atlasLinkCatalog: { entries: [] },
  }), "text/html");
}

// Exact minimal projection of the frozen public автобус record's affected fields.
// Input SHA-256: 4b0ca6352e6710d771c33390bbcf2aab6d544f38054aed8b3dbad53676ac6cf5.
// Runtime atlas-v1-90605067cb27589f; no translation book/term provenance exists.
const publicInput: Enrichment = {
  translation: { en: ["bus", "coach (long-distance bus)"], source: "learner_english_gloss", pos: "noun" },
  examples: [{ uk: "Сашко́ ї́здить в шко́лу авто́бусом.", en: "Sashko goes to school by bus.",
    source: "Anna Ohoiko", locator: "ohoiko-1000-words entry 3" }],
};

describe("borrowed quotation attribution (#11340)", () => {
  test("public runtime example is quoted with its own author, book and locator", () => {
    const doc = render(publicInput);
    const example = doc.querySelector(".example-item");
    expect(example?.querySelector("blockquote .example-uk")?.textContent).toBe(publicInput.examples?.[0].uk);
    expect(example?.querySelector("blockquote .example-en")?.textContent).toBe(publicInput.examples?.[0].en);
    expect(example?.textContent).toContain("Anna Ohoiko");
    expect(example?.querySelector("cite")?.textContent).toBe("1000 Most Useful Ukrainian Words");
    expect(example?.textContent).toContain("ohoiko-1000-words entry 3");
    expect(example?.querySelector("a")?.getAttribute("href")).toBe("https://www.ukrainianlessons.com/1000words/");
  });

  test("legacy merged terms stay exact and cannot inherit the example's book or author", () => {
    const doc = render(publicInput);
    const terms = Array.from(doc.querySelectorAll(".en-term"));
    expect(terms.map((el) => el.querySelector("q")?.textContent)).toEqual(publicInput.translation?.en);
    for (const term of terms) {
      expect(term.textContent).toContain("Source unknown");
      expect(term.textContent).not.toContain("Anna Ohoiko");
      expect(term.querySelector("cite")).toBeNull();
    }
  });
});

test("produced term credits stay separate from retained dictionary senses", () => {
  const doc = render({ translation: {
    en: ["bus", "coach (long-distance bus)"], source: "learner_english_gloss", attributions: [
      { text: "bus", source: "Anna Ohoiko", source_file: "anna-ohoiko-1000-words-2nd-ed", locator: "ohoiko-1000-words entry 3" },
      { text: "coach (long-distance bus)", source: "dictionary", locator: "sense 2" },
    ],
  } });
  const terms = Array.from(doc.querySelectorAll(".en-term"));
  expect(terms[0].querySelector("q")?.textContent).toBe("bus");
  expect(terms[0].textContent).toContain("Anna Ohoiko");
  expect(terms[0].querySelector("cite")?.textContent).toBe("1000 Most Useful Ukrainian Words");
  expect(terms[0].textContent).toContain("ohoiko-1000-words entry 3");
  expect(terms[1].querySelector("q, cite")).toBeNull();
  expect(terms[1].textContent).toContain("dictionary (sense 2)");
  expect(terms[1].textContent).not.toContain("Anna Ohoiko");
});

test.each(["javascript:alert(1)", "data:text/html,<script>alert(1)</script>"])("unsafe book links %s cannot become hrefs and quotation text stays escaped", (source_url) => {
  const text = '<img src=x onerror="alert(1)"> & <script>source</script>';
  const doc = render({
    translation: { en: [text], source: "learner_english_gloss", attributions: [
      { text, source: "Anna Ohoiko", source_file: "anna-ohoiko-500-verbs", source_url, locator: text },
    ] },
    examples: [{ uk: text, en: text, source: "Anna Ohoiko", source_file: "anna-ohoiko-500-verbs", source_url, locator: text }],
  });
  const translation = doc.querySelector(".en-term");
  const example = doc.querySelector(".example-item");
  expect(translation?.querySelector("q")?.textContent).toBe(text);
  expect(example?.querySelector("blockquote .example-uk")?.textContent).toBe(text);
  expect(example?.querySelector("blockquote .example-en")?.textContent).toBe(text);
  for (const element of [translation, example]) {
    expect(element?.querySelector("script, img, a")).toBeNull();
    expect(element?.querySelector("cite")?.textContent).toBe("500+ Ukrainian Verbs: Conjugation and Examples of Use");
    expect(element?.textContent).toContain(`(${text})`);
  }
});

test("unknown Ohoiko book stays explicit while other sources keep their original rendering", () => {
  const doc = render({ examples: [
    { uk: "unchanged <text>", en: "unchanged & text", source: "Anna Ohoiko", source_file: "unsupported", source_title: "Do not guess", locator: "entry 3" },
    { uk: "other <text>", en: "other & text", source: "dictionary", locator: "page 2" },
  ], translation: { en: ["other & term"], source: "dmklinger" } });
  const examples = Array.from(doc.querySelectorAll(".example-item"));
  expect(examples[0].querySelector("blockquote")).not.toBeNull();
  expect(examples[0].textContent).toContain("Anna Ohoiko · Book unknown (entry 3)");
  expect(examples[0].querySelector("cite, a")).toBeNull();
  expect(examples[0].textContent).not.toContain("Do not guess");
  expect(examples[1].querySelector("blockquote, cite, a")).toBeNull();
  expect(examples[1].querySelector(".example-uk")?.textContent).toBe("other <text>");
  expect(examples[1].querySelector(".atlas-muted")?.textContent).toBe("Джерело: dictionary (page 2)");
  expect(doc.querySelector(".en-term")?.textContent).toBe("other & term");
  expect(doc.querySelector(".en-term q")).toBeNull();
});

test("missing example metadata is quoted with explicit unknown provenance", () => {
  const doc = render({ examples: [{ uk: "unchanged", en: "unchanged", source: "" }] });
  expect(doc.querySelector(".example-item blockquote")).not.toBeNull();
  expect(doc.querySelector(".example-item")?.textContent).toContain("Source unknown · Book unknown");
});

test("a supported source link and each book credit survive when one term appears in both books", () => {
  const doc = render({ translation: { en: ["same"], source: "learner_english_gloss", attributions: [
    { text: "same", source: "Anna Ohoiko", source_file: "anna-ohoiko-1000-words-2nd-ed", source_url: "https://example.org/book#entry-3" },
    { text: "same", source: "Anna Ohoiko", source_file: "anna-ohoiko-500-verbs" },
  ] } });
  expect(doc.querySelectorAll(".en-term q")).toHaveLength(1);
  expect(Array.from(doc.querySelectorAll(".en-term cite")).map((el) => el.textContent)).toEqual([
    "1000 Most Useful Ukrainian Words", "500+ Ukrainian Verbs: Conjugation and Examples of Use",
  ]);
  expect(doc.querySelector(".en-term a")?.getAttribute("href")).toBe("https://example.org/book#entry-3");
  expect(doc.querySelector(".en-term a")?.getAttribute("rel")).toBe("noopener noreferrer");
});
