// @vitest-environment happy-dom

import { describe, expect, test } from "vitest";
import { renderWordAtlasArticle } from "../helpers/render-word-atlas-article";
import type { EntryRecord } from "@site/src/lib/lexicon/atlas-data-source";

describe("WordAtlasArticle heteronym support (#8022)", () => {
  const heteronymRecord: EntryRecord = {
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

  test("renders heteronym switcher bar when entry has multiple heteronyms", () => {
    const html = renderWordAtlasArticle({
      record: heteronymRecord,
      generatedAt: "2026-09-13T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const nav = doc.querySelector(".atlas-heteronym-nav");
    expect(nav).not.toBeNull();

    const tabs = nav!.querySelectorAll(".atlas-heteronym-tab");
    expect(tabs.length).toBe(2);

    expect(tabs[0].textContent).toContain("горо́д");
    expect(tabs[0].textContent).toContain("ділянка землі (A2)");
    expect(tabs[0].classList.contains("active")).toBe(true);

    expect(tabs[1].textContent).toContain("го́род");
    expect(tabs[1].textContent).toContain("заст. місто");
    expect(tabs[1].classList.contains("active")).toBe(false);
  });

  test("default heteronym renders correct title, gloss, and distinction note", () => {
    const html = renderWordAtlasArticle({
      record: heteronymRecord,
      generatedAt: "2026-09-13T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const title = doc.querySelector(".word-title");
    expect(title?.textContent).toContain("горо́д");

    const pos = doc.querySelector(".word-pos");
    expect(pos?.textContent).toContain("vegetable garden");

    const hatnote = doc.querySelector(".atlas-heteronym-hatnote");
    expect(hatnote?.textContent).toContain("Не плутати з омографом «го́род»");
    expect(hatnote?.textContent).toContain("Перейти до «го́род» →");
  });

  test("standard entry without heteronyms does not render switcher nav", () => {
    const standardRecord: EntryRecord = {
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

  test("initializes to heteronym matching window.location.hash", () => {
    window.location.hash = "#го́род";
    const html = renderWordAtlasArticle({
      record: heteronymRecord,
      generatedAt: "2026-09-13T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const title = doc.querySelector(".word-title");
    expect(title?.textContent).toContain("го́род");

    const pos = doc.querySelector(".word-pos");
    expect(pos?.textContent).toContain("city, town, fortified settlement");

    const tabs = doc.querySelectorAll(".atlas-heteronym-tab");
    expect(tabs[1].classList.contains("active")).toBe(true);
    expect(tabs[0].classList.contains("active")).toBe(false);

    window.location.hash = "";
  });
});
