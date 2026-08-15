// @vitest-environment happy-dom

/**
 * #6823 — Word-page hero lemma/CTA must stay white on the teal band.
 *
 * Live cascade: `.lu-content h1` (0,1,1) beat bare `.word-title` (0,1,0), and
 * `.lu-content .word-atlas a` (0,2,1) beat `.word-hero .practice-cta-hero` (0,2,0).
 * This test mounts the competing production rules and asserts computed colors.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, test } from "vitest";

const root = process.cwd();
const courseCss = readFileSync(resolve(root, "src/styles/course.css"), "utf8");
const atlasCss = readFileSync(resolve(root, "src/styles/word-atlas.css"), "utf8");
const customCss = readFileSync(resolve(root, "src/css/custom.css"), "utf8");

function extractRule(css: string, selector: string): string {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp(`${escaped}\\s*\\{[^}]+\\}`);
  const match = css.match(re);
  if (!match) {
    throw new Error(`Missing CSS rule for selector: ${selector}`);
  }
  return match[0];
}

function extractTokenBlock(css: string, opener: string): string {
  const start = css.indexOf(opener);
  if (start < 0) {
    throw new Error(`Missing token block starting with: ${opener}`);
  }
  const brace = css.indexOf("{", start);
  let depth = 0;
  for (let i = brace; i < css.length; i++) {
    if (css[i] === "{") depth++;
    else if (css[i] === "}") {
      depth--;
      if (depth === 0) return css.slice(start, i + 1);
    }
  }
  throw new Error(`Unclosed token block: ${opener}`);
}

function extractLuContentHeadingRule(css: string): string {
  const match = css.match(
    /\.lu-content h1,\s*\n\.lu-content h2,\s*\n\.lu-content h3\s*\{[^}]+\}/,
  );
  if (!match) {
    throw new Error("course.css missing .lu-content h1/h2/h3 color rule");
  }
  return match[0];
}

/** Production cascade slice that reproduces the #6823 specificity fight. */
function productionHeroCascadeCss(): string {
  return [
    extractTokenBlock(customCss, ":root {"),
    extractTokenBlock(customCss, "[data-theme='dark'] {"),
    extractLuContentHeadingRule(courseCss),
    extractRule(courseCss, ".lu-content a"),
    extractRule(atlasCss, ".lu-content .word-atlas a"),
    extractRule(atlasCss, ".word-hero"),
    extractRule(atlasCss, ".word-hero .word-title"),
    extractRule(atlasCss, ".word-hero .word-stress"),
    extractRule(atlasCss, ".lu-content .word-atlas .word-hero .practice-cta-hero"),
    extractRule(
      atlasCss,
      "html[data-theme='dark'] .lu-content .word-atlas .word-hero .practice-cta-hero",
    ),
  ].join("\n");
}

function injectCss(css: string): void {
  document.querySelectorAll("style[data-test-atlas-hero-contrast]").forEach((el) => el.remove());
  const style = document.createElement("style");
  style.setAttribute("data-test-atlas-hero-contrast", "production");
  style.textContent = css;
  document.head.appendChild(style);
}

function mountHero(theme: "light" | "dark"): {
  title: HTMLElement;
  stress: HTMLElement;
  cta: HTMLElement;
} {
  if (theme === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }

  document.body.innerHTML = `
    <main class="lu-content">
      <div class="word-atlas">
        <div class="word-hero">
          <h1 class="word-title">
            подаватися
            <span class="word-stress">[подавáтися]</span>
          </h1>
          <a class="practice-cta-hero" href="/words-of-the-day/practice/?lemmaId=%D0%BF%D0%BE%D0%B4%D0%B0%D0%B2%D0%B0%D1%82%D0%B8%D1%81%D1%8F">
            Practice this word →
          </a>
        </div>
      </div>
    </main>
  `;

  return {
    title: document.querySelector("h1.word-title") as HTMLElement,
    stress: document.querySelector(".word-stress") as HTMLElement,
    cta: document.querySelector("a.practice-cta-hero") as HTMLElement,
  };
}

function isWhite(color: string): boolean {
  const normalized = color.trim().toLowerCase();
  return (
    normalized === "#fff" ||
    normalized === "#ffffff" ||
    normalized === "rgb(255, 255, 255)" ||
    normalized === "rgba(255, 255, 255, 1)" ||
    normalized === "white"
  );
}

function isNearBlackText(color: string): boolean {
  // Live bug: --lu-text painted as rgb(33,33,33) / #1c1e21 on teal.
  return /rgb\(\s*(28|33)\s*,\s*(30|33)\s*,\s*(33)\s*\)/i.test(color) || /#1c1e21/i.test(color);
}

function isPrimaryBlue(color: string): boolean {
  return /rgb\(\s*0\s*,\s*87\s*,\s*(183|184)\s*\)/i.test(color) || /#0057b[78]/i.test(color);
}

afterEach(() => {
  document.body.innerHTML = "";
  document.documentElement.removeAttribute("data-theme");
  document.querySelectorAll("style[data-test-atlas-hero-contrast]").forEach((el) => el.remove());
});

describe("atlas word-hero contrast (#6823)", () => {
  test("selectors beat course/atlas content chrome (source contract)", () => {
    // Title: (0,2,0) > .lu-content h1 (0,1,1)
    expect(atlasCss).toMatch(/\.word-hero\s+\.word-title\s*\{[^}]*color:\s*#fff/s);
    // Stress: explicit white so it does not inherit a losing title color
    expect(atlasCss).toMatch(/\.word-hero\s+\.word-stress\s*\{[^}]*color:\s*#fff/s);
    // CTA: (0,4,0) > .lu-content .word-atlas a (0,2,1)
    expect(atlasCss).toMatch(
      /\.lu-content\s+\.word-atlas\s+\.word-hero\s+\.practice-cta-hero\s*\{[^}]*color:\s*#fff/s,
    );
    // Guard against reintroducing the losing bare selectors as the color owners.
    expect(atlasCss).not.toMatch(/(?:^|\n)\.word-title\s*\{[^}]*color:/);
    expect(atlasCss).not.toMatch(
      /(?:^|\n)\.word-hero\s+\.practice-cta-hero\s*\{[^}]*color:/,
    );
  });

  test("computed colors stay white on the teal band (light + dark)", () => {
    injectCss(productionHeroCascadeCss());

    for (const theme of ["light", "dark"] as const) {
      const { title, stress, cta } = mountHero(theme);

      const titleColor = getComputedStyle(title).color;
      const stressColor = getComputedStyle(stress).color;
      const ctaColor = getComputedStyle(cta).color;

      // Quote computed colors in the assertion message for acceptance evidence.
      expect(isWhite(titleColor), `${theme} h1.word-title → ${titleColor}`).toBe(true);
      expect(isWhite(stressColor), `${theme} .word-stress → ${stressColor}`).toBe(true);
      expect(isWhite(ctaColor), `${theme} a.practice-cta-hero → ${ctaColor}`).toBe(true);

      // Not the losing cascade colors from the live bug report.
      expect(isNearBlackText(titleColor), `${theme} title must not be --lu-text (${titleColor})`).toBe(
        false,
      );
      expect(isPrimaryBlue(ctaColor), `${theme} CTA must not be --blue (${ctaColor})`).toBe(false);
    }
  });

  test("legacy weak selectors would lose to course.css (mutation guard)", () => {
    // Reproduce the pre-fix cascade: bare .word-title + .word-hero .practice-cta-hero.
    // Use a literal blue (not var(--blue)) so the competing rule is always applied even
    // without the full .word-atlas token block — matching the live specificity fight.
    const losingCascade = [
      extractTokenBlock(customCss, ":root {"),
      extractLuContentHeadingRule(courseCss),
      `.lu-content .word-atlas a { color: #0057B7; }`,
      `.word-hero { background: var(--lu-id-lexicon); color: white; }`,
      `.word-title { color: #fff; }`,
      `.word-hero .practice-cta-hero { color: #fff; }`,
    ].join("\n");

    injectCss(losingCascade);
    const { title, cta } = mountHero("light");

    const titleColor = getComputedStyle(title).color;
    const ctaColor = getComputedStyle(cta).color;
    expect(isWhite(titleColor), `legacy .word-title loses → ${titleColor}`).toBe(false);
    expect(isWhite(ctaColor), `legacy .word-hero .practice-cta-hero loses → ${ctaColor}`).toBe(
      false,
    );
    expect(isPrimaryBlue(ctaColor) || ctaColor.toLowerCase() === "#0057b7", `CTA → ${ctaColor}`).toBe(
      true,
    );
  });
});
