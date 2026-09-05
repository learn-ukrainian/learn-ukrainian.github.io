// @vitest-environment node

import { readFileSync } from "node:fs";
import reactRenderer from "@astrojs/react/server.js";
import { experimental_AstroContainer as AstroContainer } from "astro/container";
import { Window } from "happy-dom";
import { beforeAll, describe, expect, test } from "vitest";

describe("practice load-error locale purity (#7691)", () => {
  let html: string;
  const layout = readFileSync("src/layouts/CourseLayout.astro", "utf8");
  const localeCss = layout.match(/[^{}]*\.lu-i18n \[data-loc=[^{}]+\{[^}]+\}/g)!.join("\n");

  beforeAll(async () => {
    const { default: Mount } = await import("@site/src/lexicon/LexiconPracticeMount.astro");
    const container = await AstroContainer.create();
    container.addServerRenderer({ renderer: reactRenderer });
    container.addClientRenderer({ name: "@astrojs/react", entrypoint: "@astrojs/react/client.js" });
    html = await container.renderToString(Mount);
  });

  test.each([
    ["en", "We couldn’t load practice.", "Try again"],
    ["uk", "Не вдалося завантажити практику.", "Спробувати ще раз"],
  ])("shows only %s error and retry labels", (locale, error, retry) => {
    const window = new Window();
    try {
      const { document } = window;
      document.documentElement.dataset.chromeLocale = locale;
      document.head.innerHTML = `<style>${localeCss}</style>`;
      document.body.innerHTML = html;
      const fallback = document.querySelector<HTMLElement>("#lexicon-practice-fallback")!;
      expect(fallback.hidden).toBe(true);
      fallback.hidden = false;

      for (const [selector, key, expected] of [
        ["#lexicon-practice-error", "practice.loadError", error],
        ["button", "practice.retry", retry],
      ]) {
        const label = fallback.querySelector(selector)!;
        expect(label.querySelector(".lu-i18n")?.getAttribute("data-i18n")).toBe(key);
        const variants = [...label.querySelectorAll<HTMLElement>("[data-loc]")];
        expect(variants).toHaveLength(2);
        const visible = variants.filter((span) => window.getComputedStyle(span).display !== "none");
        expect(visible).toHaveLength(1);
        expect(visible[0].dataset.loc).toBe(locale);
        expect(visible[0].lang).toBe(locale);
        expect(visible[0].textContent).toBe(expected);
        expect(label.textContent).not.toContain("/");
      }
    } finally {
      window.happyDOM.abort();
    }
  });
});
