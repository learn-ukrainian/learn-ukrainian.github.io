// @vitest-environment happy-dom

/**
 * PR3 R6 — hostile EntryRecord fixtures must not execute markup or javascript: URLs.
 * React text sinks escape HTML; safeHref rejects non-http(s)/relative schemes.
 */
import { describe, expect, test } from "vitest";
import type { EntryRecord } from "@site/src/lib/lexicon/atlas-data-source";
import { safeHref } from "@site/src/lib/lexicon/safe-url";
import { renderWordAtlasArticle } from "../helpers/render-word-atlas-article";
import { articleProps } from "../helpers/word-atlas-record";

function hostileGlossRecord(): EntryRecord {
  return articleProps({
    lemma: "тест",
    url_slug: "hostile-gloss",
    gloss: '<script>alert("xss-gloss")</script>',
    entry_type: "lemma",
    pos: "noun",
    ipa: null,
    primary_source: "hostile-fixture",
    course_usage: [],
    enrichment: {
      etymology: {
        text: 'safe prefix <script>alert("xss-ety")</script> suffix',
        source: "hostile-etymology",
      },
      meaning: {
        definitions: ['<img src=x onerror=alert(1)> definition'],
        source: "hostile-meaning",
      },
    },
  }).record;
}

function hostileUrlRecord(): EntryRecord {
  return articleProps({
    lemma: "лінк",
    url_slug: "hostile-url",
    gloss: "link probe",
    entry_type: "lemma",
    pos: "noun",
    ipa: null,
    primary_source: "hostile-fixture",
    course_usage: [],
    enrichment: {
      definition_cards: [
        {
          id: "sum20-hostile",
          source: "СУМ-20",
          source_pill: "СУМ-20",
          definitions: ["чисте визначення"],
          source_url: "javascript:alert('xss-card')",
        },
      ],
      literary_attestation: {
        text: "цитата",
        source: "corpus",
        source_label: "Корпус",
        source_url: "javascript:alert('xss-lit')",
      },
      external_materials: [
        {
          title: "Злий матеріал",
          url: "javascript:alert('xss-ext')",
          kind: "blog",
        },
      ],
      translation: { en: ["link"], source: "hostile" },
    },
    wiki_reference: {
      wikipedia: {
        title: "Wiki",
        summary: "summary",
        url: "javascript:alert('xss-wiki')",
      },
      wiktionary_url: "javascript:alert('xss-wikt')",
      wikisource_url: null,
      attribution: "hostile",
    },
    sections: {
      synonyms: {
        items: ["а"],
        source: "hostile",
        source_urls: ["javascript:alert('xss-syn')"],
      },
    },
  }).record;
}

describe("WordAtlasArticle XSS boundary (PR3 R6)", () => {
  test("safeHref rejects javascript: and data: URLs", () => {
    expect(safeHref("javascript:alert(1)")).toBeNull();
    expect(safeHref("JAVASCRIPT:alert(1)")).toBeNull();
    expect(safeHref("data:text/html,<script>x</script>")).toBeNull();
    expect(safeHref("vbscript:msgbox(1)")).toBeNull();
    expect(safeHref("https://uk.wikipedia.org/wiki/Тест")).toMatch(/^https:/);
    expect(safeHref("/lexicon/foo/")).toBe("/lexicon/foo/");
  });

  test("script tags in gloss/etymology/meaning render as escaped text, not markup", () => {
    const html = renderWordAtlasArticle({
      record: hostileGlossRecord(),
      generatedAt: "test",
      manifestVersion: "test",
    });
    expect(html).not.toContain("<script>");
    expect(html).not.toContain('alert("xss-gloss")');
    // Escaped entities must appear (React text escaping).
    expect(html).toMatch(/&lt;script&gt;/);
    expect(html).toContain("xss-gloss");
    expect(html).toContain("xss-ety");
    expect(html).not.toContain("<img src=x");
    expect(html).toMatch(/&lt;img/);
  });

  test("javascript: URLs are neutralized (no href with javascript:)", () => {
    const html = renderWordAtlasArticle({
      record: hostileUrlRecord(),
      generatedAt: "test",
      manifestVersion: "test",
    });
    expect(html.toLowerCase()).not.toContain("javascript:");
    // Card/source pills fall back to non-link spans when URL is unsafe.
    expect(html).toContain("СУМ-20");
    expect(html).toContain("Злий матеріал");
    // Title remains text; must not be wrapped in an anchor to javascript:
    expect(html).not.toMatch(/href\s*=\s*["']javascript:/i);
  });
});
