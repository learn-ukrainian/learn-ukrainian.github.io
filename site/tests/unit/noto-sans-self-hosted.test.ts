/**
 * Regression: CourseLayout typography must not depend on Google Fonts CDN.
 * Retired fonts.gstatic.com Noto Sans v42 URLs 404'd and failed the
 * `/words-of-the-day/` Playwright console-error assertion.
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { describe, expect, test } from "vitest";

const GOOGLE_FONTS_HOSTS = ["fonts.googleapis.com", "fonts.gstatic.com"];
const CUSTOM_CSS = resolve(process.cwd(), "src/css/custom.css");
const DIST_DIR = resolve(process.cwd(), "dist");
const PACKAGE_JSON = resolve(process.cwd(), "package.json");

function collectFiles(dir: string, extensions: Set<string>): string[] {
  if (!existsSync(dir)) return [];
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...collectFiles(path, extensions));
    } else if ([...extensions].some((ext) => entry.name.endsWith(ext))) {
      out.push(path);
    }
  }
  return out;
}

describe("Noto Sans self-hosted (no Google Fonts runtime)", () => {
  test("package.json depends on @fontsource/noto-sans", () => {
    const pkg = JSON.parse(readFileSync(PACKAGE_JSON, "utf8")) as {
      dependencies?: Record<string, string>;
    };
    expect(pkg.dependencies?.["@fontsource/noto-sans"]).toMatch(/^\^?5\./);
  });

  test("custom.css self-hosts Noto Sans weights via Fontsource (unicode-range CSS)", () => {
    const css = readFileSync(CUSTOM_CSS, "utf8");

    // Comments may name the retired hosts; runtime @import/url must not.
    expect(css).not.toMatch(
      /@import\s+url\(['"]?https?:\/\/fonts\.(googleapis|gstatic)\.com/i,
    );
    expect(css).not.toMatch(
      /url\(['"]?https?:\/\/fonts\.(googleapis|gstatic)\.com/i,
    );
    expect(css).not.toMatch(/@import\s+url\(['"]?https?:\/\//i);
    expect(css).toContain("@fontsource/noto-sans/400.css");
    expect(css).toContain("@fontsource/noto-sans/400-italic.css");
    expect(css).toContain("@fontsource/noto-sans/600.css");
    expect(css).toContain("@fontsource/noto-sans/700.css");
  });

  test("Fontsource weight CSS ships Cyrillic unicode-range for Ukrainian glyphs", () => {
    const weightCss = resolve(
      process.cwd(),
      "node_modules/@fontsource/noto-sans/400.css",
    );
    expect(existsSync(weightCss)).toBe(true);
    const css = readFileSync(weightCss, "utf8");
    expect(css).toContain("noto-sans-cyrillic-400-normal");
    // Cyrillic block is typically listed after combining marks (e.g. U+0301,…).
    expect(css).toMatch(/unicode-range:[^;]*U\+0400-045F/i);
  });

  test.skipIf(collectFiles(DIST_DIR, new Set([".css", ".html"])).length === 0)(
    "built dist CSS/HTML has no Google Fonts host references when dist/ is present",
    () => {
      const files = collectFiles(DIST_DIR, new Set([".css", ".html"]));
      expect(files.length).toBeGreaterThan(0);

      const offenders: string[] = [];
      for (const file of files) {
        const text = readFileSync(file, "utf8");
        if (GOOGLE_FONTS_HOSTS.some((host) => text.includes(host))) {
          offenders.push(file.replace(process.cwd() + "/", ""));
        }
      }
      expect(offenders).toEqual([]);
    },
  );
});
