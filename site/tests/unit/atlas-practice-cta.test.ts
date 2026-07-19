// @vitest-environment happy-dom

/**
 * #5435 — Atlas entry CTA: practice this word (presence + deep-link routing).
 */
import { describe, expect, test } from "vitest";
import {
  ATLAS_PRACTICE_LEMMA_PARAM,
  ATLAS_PRACTICE_PATH,
  atlasPracticeHref,
} from "@site/src/lib/lexicon/atlas-practice-link";
import { CHROME_STRINGS } from "@site/src/lib/i18n/chrome";
import { renderWordAtlasArticle } from "../helpers/render-word-atlas-article";
import { articleProps } from "../helpers/word-atlas-record";

function lemmaEntry(overrides: { lemma?: string; url_slug?: string } = {}) {
  const lemma = overrides.lemma ?? "кава";
  return {
    lemma,
    url_slug: overrides.url_slug ?? lemma,
    gloss: "coffee",
    entry_type: "lemma" as const,
    pos: "noun",
    ipa: null,
    primary_source: "test",
    course_usage: [],
    enrichment: null,
  };
}

function parseHref(html: string, testId: string): string | null {
  const doc = new DOMParser().parseFromString(html, "text/html");
  const el = doc.querySelector(`[data-testid="${testId}"]`);
  if (!el) return null;
  return el.getAttribute("href");
}

describe("atlasPracticeHref contract", () => {
  test("builds Practice hub URL with encoded lemmaId query param", () => {
    const href = atlasPracticeHref("кава");
    expect(href.startsWith(ATLAS_PRACTICE_PATH)).toBe(true);
    const url = new URL(href, "https://example.test");
    expect(url.pathname).toBe(ATLAS_PRACTICE_PATH);
    expect(url.searchParams.get(ATLAS_PRACTICE_LEMMA_PARAM)).toBe("кава");
    // Explicit encoding in the serialized query (not raw Cyrillic only).
    expect(href).toContain("lemmaId=");
    expect(decodeURIComponent(href.split("lemmaId=")[1] ?? "")).toBe("кава");
  });

  test("trims whitespace and returns bare path for empty id", () => {
    expect(atlasPracticeHref("  knyha  ")).toBe(
      `${ATLAS_PRACTICE_PATH}?${ATLAS_PRACTICE_LEMMA_PARAM}=knyha`,
    );
    expect(atlasPracticeHref("")).toBe(ATLAS_PRACTICE_PATH);
    expect(atlasPracticeHref("   ")).toBe(ATLAS_PRACTICE_PATH);
  });
});

describe("WordAtlasArticle practice CTA (#5435)", () => {
  test("shows active dual-language CTA linking to practice when lemma is in pool", () => {
    const html = renderWordAtlasArticle(
      articleProps(lemmaEntry({ lemma: "кава", url_slug: "кава" }), {
        practiceLevels: ["A1"],
      }),
    );

    const doc = new DOMParser().parseFromString(html, "text/html");
    const cta = doc.querySelector('[data-testid="atlas-practice-cta"]');
    expect(cta).not.toBeNull();
    expect(cta?.getAttribute("data-practice-available")).toBe("true");
    expect(cta?.tagName.toLowerCase()).toBe("a");

    const href = cta?.getAttribute("href");
    expect(href).toBe(atlasPracticeHref("кава"));
    expect(href).toContain("/words-of-the-day/practice/");
    expect(new URL(href!, "https://example.test").searchParams.get("lemmaId")).toBe("кава");

    // Dual-render chrome (FOUC-safe): both locales present in markup.
    const en = cta?.querySelector('[data-loc="en"]');
    const uk = cta?.querySelector('[data-loc="uk"]');
    expect(en?.textContent).toBe(CHROME_STRINGS.en["atlas.practiceThisWord"]);
    expect(uk?.textContent).toBe(CHROME_STRINGS.uk["atlas.practiceThisWord"]);
    expect(doc.querySelector('[data-testid="atlas-practice-cta-unavailable"]')).toBeNull();
  });

  test("shows honest disabled/hint state when lemma is not in practice pool", () => {
    const html = renderWordAtlasArticle(
      articleProps(lemmaEntry({ lemma: "рідкісний", url_slug: "рідкісний" }), {
        practiceLevels: [],
      }),
    );

    const doc = new DOMParser().parseFromString(html, "text/html");
    const hint = doc.querySelector('[data-testid="atlas-practice-cta-unavailable"]');
    expect(hint).not.toBeNull();
    expect(hint?.getAttribute("data-practice-available")).toBe("false");
    expect(hint?.getAttribute("role")).toBe("status");
    expect(hint?.className).toContain("practice-cta-hero--disabled");
    expect(hint?.tagName.toLowerCase()).toBe("span");
    expect(hint?.getAttribute("href")).toBeNull();

    const en = hint?.querySelector('[data-loc="en"]');
    const uk = hint?.querySelector('[data-loc="uk"]');
    expect(en?.textContent).toBe(CHROME_STRINGS.en["atlas.practiceUnavailable"]);
    expect(uk?.textContent).toBe(CHROME_STRINGS.uk["atlas.practiceUnavailable"]);
    expect(doc.querySelector('[data-testid="atlas-practice-cta"]')).toBeNull();
  });

  test("does not show practice CTA on form-of redirect pages", () => {
    const html = renderWordAtlasArticle(
      articleProps({
        lemma: "книзі",
        url_slug: "книзі",
        gloss: null,
        entry_type: null,
        pos: null,
        ipa: null,
        primary_source: "test",
        course_usage: [],
        enrichment: null,
        form_of: { lemma: "книга", url_slug: "книга" },
      }),
    );

    const doc = new DOMParser().parseFromString(html, "text/html");
    expect(doc.querySelector('[data-testid="atlas-practice-cta"]')).toBeNull();
    expect(doc.querySelector('[data-testid="atlas-practice-cta-unavailable"]')).toBeNull();
  });

  test("routes latinized lemmaId slug into practice query", () => {
    const html = renderWordAtlasArticle(
      articleProps(lemmaEntry({ lemma: "книга", url_slug: "knyha" }), {
        practiceLevels: ["A1", "A2"],
      }),
    );
    expect(parseHref(html, "atlas-practice-cta")).toBe(atlasPracticeHref("knyha"));
  });
});
