// @vitest-environment happy-dom

import { describe, expect, test } from "vitest";
import { renderWordAtlasArticle } from "../helpers/render-word-atlas-article";
import type { EntryRecord } from "@site/src/lib/lexicon/atlas-data-source";
import { bindHeteronymHandlers } from "@site/src/lexicon/WordAtlasClientShell";

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

  test("automatically applies curated heteronyms when record.entry.heteronyms is absent from shard (live fallback for город)", () => {
    // Mimics the live runtime shard for 'город' where record.entry.heteronyms is undefined
    const liveShardRecord: EntryRecord = {
      slug: "город",
      kind: "article",
      entry: {
        lemma: "город",
        url_slug: "город",
        gloss: "vegetable garden",
        pos: "noun",
        heritage_status: {
          classification: "authentic-archaism",
        },
        enrichment: {
          stress: { form: "го́род" },
        },
        sections: {
          synonyms: { items: ["місто"] },
        },
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
      record: liveShardRecord,
      generatedAt: "2026-09-13T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    // Must render the heteronym nav bar
    const nav = doc.querySelector(".atlas-heteronym-nav");
    expect(nav).not.toBeNull();
    const tabs = nav!.querySelectorAll(".atlas-heteronym-tab");
    expect(tabs.length).toBe(2);
    expect(tabs[0].textContent).toContain("горо́д");
    expect(tabs[1].textContent).toContain("го́род");

    // Must render the primary panel with modern standard (A2 vegetable garden)
    const panel0 = doc.querySelector("#heteronym-panel-0");
    expect(panel0?.textContent).toContain("горо́д");
    expect(panel0?.textContent).toContain("vegetable garden");
    expect(panel0?.textContent).toContain("A2");
    expect(panel0?.textContent).toContain("грядка");

    // Must render the second panel with archaic city
    const panel1 = doc.querySelector("#heteronym-panel-1");
    expect(panel1?.textContent).toContain("го́род");
    expect(panel1?.textContent).toContain("archaic");
    expect(panel1?.textContent).toContain("місто");
  });

  test("automatically applies curated heteronyms for batch expansion lemma (live fallback for обід, #8039)", () => {
    const obidRecord: EntryRecord = {
      slug: "обід",
      kind: "article",
      entry: {
        lemma: "обід",
        url_slug: "обід",
        gloss: "lunch",
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
      record: obidRecord,
      generatedAt: "2026-09-14T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const nav = doc.querySelector(".atlas-heteronym-nav");
    expect(nav).not.toBeNull();
    const tabs = nav!.querySelectorAll(".atlas-heteronym-tab");
    expect(tabs.length).toBe(2);
    expect(tabs[0].textContent).toContain("о́бід");
    expect(tabs[0].textContent).toContain("у колеса");
    expect(tabs[1].textContent).toContain("обі́д");
    expect(tabs[1].textContent).toContain("споживання їжі (A1)");

    const panel0 = doc.querySelector("#heteronym-panel-0");
    expect(panel0?.textContent).toContain("о́бід");
    expect(panel0?.textContent).toContain("rim");

    const panel1 = doc.querySelector("#heteronym-panel-1");
    expect(panel1?.textContent).toContain("обі́д");
    expect(panel1?.textContent).toContain("lunch");
  });

  test("renders sense-specific definitions and prevents definition leakage across heteronym senses (опій, #8039)", () => {
    const opiyRecord: EntryRecord = {
      slug: "опій",
      kind: "article",
      entry: {
        lemma: "опій",
        url_slug: "опій",
        gloss: "opium",
        pos: "noun",
        enrichment: {
          meaning: {
            definitions: ["BASE_PROBE_MARKER_OPIUM"],
            source: "Base Source",
          },
          definition_cards: [
            {
              id: "probe-base-card",
              source: "Base Probe Source",
              definitions: ["BASE_PROBE_CARD_MARKER"],
            },
          ],
        },
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
      record: opiyRecord,
      generatedAt: "2026-09-15T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const panel0 = doc.querySelector("#heteronym-panel-0");
    const panel1 = doc.querySelector("#heteronym-panel-1");

    expect(panel0).not.toBeNull();
    expect(panel1).not.toBeNull();

    const panel0Def = panel0?.querySelector(".def-card.sum20 .def-text")?.textContent;
    const panel1Def = panel1?.querySelector(".def-card.sum20 .def-text")?.textContent;

    // Tab 0 must render sense 1 definition (opium) and NOT horse hoof disease
    expect(panel0?.textContent).toContain("о́пій");
    expect(panel0Def).toContain("опійного маку");
    expect(panel0Def).not.toContain("запалення копит");

    // Tab 1 must render sense 2 definition (horse hoof inflammation) and NOT sense 1 or base probe markers
    expect(panel1?.textContent).toContain("опі́й");
    expect(panel1Def).toContain("запалення копит");
    expect(panel1Def).not.toContain("опійного маку");
    expect(panel1?.textContent).not.toContain("BASE_PROBE_MARKER_OPIUM");
    expect(panel1?.textContent).not.toContain("BASE_PROBE_CARD_MARKER");
  });

  test("isolates sense definitions and preserves null Soviet colonization context (ланець, #8039)", () => {
    const lanetsRecord: EntryRecord = {
      slug: "ланець",
      kind: "article",
      entry: {
        lemma: "ланець",
        url_slug: "ланець",
        gloss: "ragged person",
        pos: "noun",
        enrichment: {
          meaning: {
            definitions: ["BASE_RAGGED_PERSON_MEANING"],
            source: "Base Source",
          },
        },
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
      record: lanetsRecord,
      generatedAt: "2026-09-15T00:00:00Z",
      manifestVersion: "1.0",
    });
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const panel0 = doc.querySelector("#heteronym-panel-0");
    const panel1 = doc.querySelector("#heteronym-panel-1");

    expect(panel0).not.toBeNull();
    expect(panel1).not.toBeNull();

    // Tab 0: ragged person, СУМ-11 colonization context present
    expect(panel0?.textContent).toContain("ла́нець");
    expect(panel0?.textContent).toContain("Одягнена в лахміття людина");
    expect(panel0?.textContent).not.toContain("Ланцюг.");

    // Tab 1: chain, no ragged person meaning, NO Soviet colonization card (explicitly null)
    expect(panel1?.textContent).toContain("лане́ць");
    expect(panel1?.textContent).toContain("Ланцюг.");
    expect(panel1?.textContent).not.toContain("Одягнена в лахміття людина");
    expect(panel1?.textContent).not.toContain("BASE_RAGGED_PERSON_MEANING");
    expect(panel1?.textContent).not.toContain("Радянський окупаційний контекст");
  });
});

describe("bindHeteronymHandlers interactive client wiring (#8022)", () => {
  function createFixture() {
    const container = document.createElement("div");
    container.innerHTML = `
      <div class="atlas-heteronym-nav" role="tablist">
        <button class="atlas-heteronym-tab active" data-heteronym-target="0" data-heteronym-headword="горо́д" role="tab" aria-selected="true" tabindex="0">горо́д</button>
        <button class="atlas-heteronym-tab" data-heteronym-target="1" data-heteronym-headword="го́род" role="tab" aria-selected="false" tabindex="-1">го́род</button>
      </div>
      <div id="heteronym-panel-0" data-heteronym-idx="0" role="tabpanel" style="display: block;">
        <button data-heteronym-jump="1">Go to го́род</button>
        <p>Garden content</p>
      </div>
      <div id="heteronym-panel-1" data-heteronym-idx="1" role="tabpanel" style="display: none;" hidden>
        <button data-heteronym-jump="0">Go to горо́д</button>
        <p>City content</p>
      </div>
    `;
    document.body.appendChild(container);
    return container;
  }

  test("clicking a tab switches active state and panels", () => {
    const container = createFixture();
    const cleanup = bindHeteronymHandlers(container);

    const tabs = container.querySelectorAll<HTMLElement>(".atlas-heteronym-tab");
    const panel0 = container.querySelector<HTMLElement>("#heteronym-panel-0")!;
    const panel1 = container.querySelector<HTMLElement>("#heteronym-panel-1")!;

    expect(tabs[0].classList.contains("active")).toBe(true);
    expect(tabs[1].classList.contains("active")).toBe(false);
    expect(panel0.style.display).toBe("block");
    expect(panel1.style.display).toBe("none");

    // Click tab 1
    tabs[1].click();

    expect(tabs[0].classList.contains("active")).toBe(false);
    expect(tabs[0].getAttribute("aria-selected")).toBe("false");
    expect(tabs[0].tabIndex).toBe(-1);

    expect(tabs[1].classList.contains("active")).toBe(true);
    expect(tabs[1].getAttribute("aria-selected")).toBe("true");
    expect(tabs[1].tabIndex).toBe(0);

    expect(panel0.style.display).toBe("none");
    expect(panel0.hasAttribute("hidden")).toBe(true);
    expect(panel1.style.display).toBe("block");
    expect(panel1.hasAttribute("hidden")).toBe(false);

    cleanup();
    container.remove();
  });

  test("keyboard navigation (ArrowRight, ArrowLeft, Home, End) cycles tabs", () => {
    const container = createFixture();
    const cleanup = bindHeteronymHandlers(container);

    const tabs = container.querySelectorAll<HTMLElement>(".atlas-heteronym-tab");
    const panel1 = container.querySelector<HTMLElement>("#heteronym-panel-1")!;

    // Focus tab 0 and press ArrowRight
    tabs[0].dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));

    expect(tabs[1].classList.contains("active")).toBe(true);
    expect(panel1.style.display).toBe("block");

    // Press ArrowRight again (wraps around to tab 0)
    tabs[1].dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
    expect(tabs[0].classList.contains("active")).toBe(true);

    // Press ArrowLeft (wraps backwards to tab 1)
    tabs[0].dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft", bubbles: true }));
    expect(tabs[1].classList.contains("active")).toBe(true);

    // Press Home (goes to tab 0)
    tabs[1].dispatchEvent(new KeyboardEvent("keydown", { key: "Home", bubbles: true }));
    expect(tabs[0].classList.contains("active")).toBe(true);

    // Press End (goes to tab 1)
    tabs[0].dispatchEvent(new KeyboardEvent("keydown", { key: "End", bubbles: true }));
    expect(tabs[1].classList.contains("active")).toBe(true);

    cleanup();
    container.remove();
  });

  test("clicking hatnote jump button activates the target tab", () => {
    const container = createFixture();
    const cleanup = bindHeteronymHandlers(container);

    const jumpBtn = container.querySelector<HTMLElement>("[data-heteronym-jump='1']")!;
    const tabs = container.querySelectorAll<HTMLElement>(".atlas-heteronym-tab");
    const panel1 = container.querySelector<HTMLElement>("#heteronym-panel-1")!;

    jumpBtn.click();

    expect(tabs[1].classList.contains("active")).toBe(true);
    expect(panel1.style.display).toBe("block");

    cleanup();
    container.remove();
  });

  test("syncs with location.hash on load and on hashchange", () => {
    window.location.hash = "#го́род";
    const container = createFixture();
    const cleanup = bindHeteronymHandlers(container);

    const tabs = container.querySelectorAll<HTMLElement>(".atlas-heteronym-tab");
    const panel1 = container.querySelector<HTMLElement>("#heteronym-panel-1")!;

    // Initial load with hash #го́род activates tab 1
    expect(tabs[1].classList.contains("active")).toBe(true);
    expect(panel1.style.display).toBe("block");

    // Fire hashchange to #горо́д
    window.location.hash = "#горо́д";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    expect(tabs[0].classList.contains("active")).toBe(true);
    const panel0 = container.querySelector<HTMLElement>("#heteronym-panel-0")!;
    expect(panel0.style.display).toBe("block");

    cleanup();
    container.remove();
    window.location.hash = "";
  });

  test("syncs with location.hash for batch heteronym headword (e.g. #обі́д, #8039)", () => {
    const container = document.createElement("div");
    container.innerHTML = `
      <div class="atlas-heteronym-nav" role="tablist">
        <button class="atlas-heteronym-tab active" data-heteronym-target="0" data-heteronym-headword="о́бід" role="tab" aria-selected="true" tabindex="0">о́бід</button>
        <button class="atlas-heteronym-tab" data-heteronym-target="1" data-heteronym-headword="обі́д" role="tab" aria-selected="false" tabindex="-1">обі́д</button>
      </div>
      <div id="heteronym-panel-0" data-heteronym-idx="0" role="tabpanel" style="display: block;">
        <button data-heteronym-jump="1">Go to обі́д</button>
        <p>Wheel rim content</p>
      </div>
      <div id="heteronym-panel-1" data-heteronym-idx="1" role="tabpanel" style="display: none;" hidden>
        <button data-heteronym-jump="0">Go to о́бід</button>
        <p>Lunch meal content</p>
      </div>
    `;
    document.body.appendChild(container);

    window.location.hash = "#обі́д";
    const cleanup = bindHeteronymHandlers(container);

    const tabs = container.querySelectorAll<HTMLElement>(".atlas-heteronym-tab");
    const panel0 = container.querySelector<HTMLElement>("#heteronym-panel-0")!;
    const panel1 = container.querySelector<HTMLElement>("#heteronym-panel-1")!;

    // Initial load with hash #обі́д activates tab 1
    expect(tabs[1].classList.contains("active")).toBe(true);
    expect(panel1.style.display).toBe("block");
    expect(panel0.style.display).toBe("none");

    // Fire hashchange to #о́бід
    window.location.hash = "#о́бід";
    window.dispatchEvent(new HashChangeEvent("hashchange"));

    expect(tabs[0].classList.contains("active")).toBe(true);
    expect(panel0.style.display).toBe("block");
    expect(panel1.style.display).toBe("none");

    cleanup();
    container.remove();
    window.location.hash = "";
  });

  test("cleanup removes event listeners", () => {
    const container = createFixture();
    const cleanup = bindHeteronymHandlers(container);

    const tabs = container.querySelectorAll<HTMLElement>(".atlas-heteronym-tab");
    cleanup();

    // After cleanup, click should not change active tab
    tabs[1].click();
    expect(tabs[1].classList.contains("active")).toBe(false);
    expect(tabs[0].classList.contains("active")).toBe(true);

    container.remove();
  });
});
