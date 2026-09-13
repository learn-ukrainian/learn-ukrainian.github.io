// @vitest-environment happy-dom

import { describe, expect, test } from "vitest";
import { renderWordAtlasArticle } from "../helpers/render-word-atlas-article";
import type { EntryRecord } from "@site/src/lib/lexicon/atlas-data-source";

describe("WordAtlasArticle heteronym support (#8022)", () => {
  const heteronymRecord: EntryRecord = {
    slug: "город",
    kind: "article",
    entry: {
      lemma: "город",
      url_slug: "город",
      gloss: "vegetable garden",
      pos: "noun",
      heteronyms: [
        {
          headword: "горо́д",
          short_label: "ділянка землі (A2)",
          gloss: "vegetable garden",
          pos: "noun",
          cefr: "A2",
          heritage_status: {
            classification: "standard",
            is_russianism: false,
            russian_shadow: false,
          },
          pronunciation: {
            ipa: "[ɦɔˈrɔd]",
            source: "VESUM",
          },
          sections: {
            synonyms: {
              items: ["грядка", "городчик"],
              source: "СУМ-20",
            },
          },
          distinction_note: "Не плутати з омографом «го́род» (наголос на першому складі: застаріле «місто», фортеця).",
        },
        {
          headword: "го́род",
          short_label: "заст. місто",
          gloss: "city, town, fortified settlement (archaic)",
          pos: "noun",
          cefr: null,
          heritage_status: {
            classification: "authentic-archaism",
            is_russianism: false,
            russian_shadow: false,
          },
          pronunciation: {
            ipa: "[ˈɦɔrɔd]",
            source: "kaikki/Wiktionary",
          },
          sections: {
            synonyms: {
              items: ["місто"],
              source: "СУМ-11: Те саме, що → місто",
            },
          },
          distinction_note: "Не плутати з сучасним словом «горо́д» (наголос на другому складі: ділянка землі біля хати).",
        },
      ],
    } as any,
    aliases: [],
    relations: [],
    provenance: [],
    renderContext: {
      practiceLevels: [],
      componentLinks: [],
    },
  };

  test("renders accessible heteronym switcher bar and panels when entry has multiple heteronyms", () => {
    const html = renderWordAtlasArticle({
      record: heteronymRecord,
      generatedAt: "2026-09-13T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const nav = doc.querySelector(".atlas-heteronym-nav");
    expect(nav).not.toBeNull();
    expect(nav?.getAttribute("role")).toBe("tablist");

    const tabs = nav!.querySelectorAll(".atlas-heteronym-tab");
    expect(tabs.length).toBe(2);

    expect(tabs[0].textContent).toContain("горо́д");
    expect(tabs[0].textContent).toContain("ділянка землі (A2)");
    expect(tabs[0].classList.contains("active")).toBe(true);
    expect(tabs[0].getAttribute("role")).toBe("tab");
    expect(tabs[0].getAttribute("aria-selected")).toBe("true");
    expect(tabs[0].getAttribute("aria-controls")).toBe("heteronym-panel-0");

    expect(tabs[1].textContent).toContain("го́род");
    expect(tabs[1].textContent).toContain("заст. місто");
    expect(tabs[1].classList.contains("active")).toBe(false);
    expect(tabs[1].getAttribute("role")).toBe("tab");
    expect(tabs[1].getAttribute("aria-selected")).toBe("false");
    expect(tabs[1].getAttribute("aria-controls")).toBe("heteronym-panel-1");

    const panels = doc.querySelectorAll(".atlas-heteronym-panel");
    expect(panels.length).toBe(2);
    expect(panels[0].id).toBe("heteronym-panel-0");
    expect(panels[1].id).toBe("heteronym-panel-1");
  });

  test("renders distinct content and hatnotes in both heteronym panels in SSR HTML", () => {
    const html = renderWordAtlasArticle({
      record: heteronymRecord,
      generatedAt: "2026-09-13T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const panel0 = doc.querySelector("#heteronym-panel-0");
    expect(panel0).not.toBeNull();
    expect(panel0?.getAttribute("style")).toBeNull();
    expect(panel0?.querySelector(".word-title")?.textContent).toContain("горо́д");
    expect(panel0?.querySelector(".word-pos")?.textContent).toContain("vegetable garden");
    expect(panel0?.querySelector(".atlas-heteronym-hatnote")?.textContent).toContain("Не плутати з омографом «го́род»");
    const jump0 = panel0?.querySelector("[data-heteronym-jump]");
    expect(decodeURIComponent(jump0?.getAttribute("href") || "")).toBe("#го́род");

    const panel1 = doc.querySelector("#heteronym-panel-1");
    expect(panel1).not.toBeNull();
    expect(panel1?.getAttribute("style")).toMatch(/display:\s*none/);
    expect(panel1?.querySelector(".word-title")?.textContent).toContain("го́род");
    expect(panel1?.querySelector(".word-pos")?.textContent).toContain("city, town, fortified settlement");
    expect(panel1?.querySelector(".atlas-heteronym-hatnote")?.textContent).toContain("Не плутати з сучасним словом «горо́д»");
    const jump1 = panel1?.querySelector("[data-heteronym-jump]");
    expect(decodeURIComponent(jump1?.getAttribute("href") || "")).toBe("#горо́д");
  });

  test("renders distinct synonyms in sections for атлас heteronyms", () => {
    const atlasRecord: EntryRecord = {
      slug: "атлас",
      kind: "article",
      entry: {
        lemma: "атлас",
        url_slug: "атлас",
        gloss: "atlas (bound collection of maps)",
        pos: "noun",
        heteronyms: [
          {
            headword: "а́тлас",
            short_label: "збірник карт",
            gloss: "atlas (bound collection of maps)",
            pos: "noun",
            sections: {
              synonyms: {
                items: ["збірник карт", "географічний атлас"],
                source: "СУМ-11",
              },
            },
          },
          {
            headword: "атла́с",
            short_label: "тканина",
            gloss: "satin (glossy silk fabric)",
            pos: "noun",
            sections: {
              synonyms: {
                items: ["шовк", "сатин"],
                source: "СУМ-11",
              },
            },
          },
        ],
      } as any,
      aliases: [],
      relations: [],
      provenance: [],
      renderContext: {
        practiceLevels: [],
        componentLinks: [],
      },
    };

    const html = renderWordAtlasArticle({
      record: atlasRecord,
      generatedAt: "2026-09-13T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const panel0 = doc.querySelector("#heteronym-panel-0");
    expect(panel0?.textContent).toContain("збірник карт");
    expect(panel0?.textContent).not.toContain("сатин");

    const panel1 = doc.querySelector("#heteronym-panel-1");
    expect(panel1?.textContent).toContain("сатин");
    expect(panel1?.textContent).not.toContain("географічний атлас");
  });

  test("standard entry without heteronyms does not render switcher nav", () => {
    const standardRecord: EntryRecord = {
      slug: "книга",
      kind: "article",
      entry: {
        lemma: "книга",
        url_slug: "книга",
        gloss: "book",
        pos: "noun",
      } as any,
      aliases: [],
      relations: [],
      provenance: [],
      renderContext: {
        practiceLevels: [],
        componentLinks: [],
      },
    };

    const html = renderWordAtlasArticle({
      record: standardRecord,
      generatedAt: "2026-09-13T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const nav = doc.querySelector(".atlas-heteronym-nav");
    expect(nav).toBeNull();
  });
});
