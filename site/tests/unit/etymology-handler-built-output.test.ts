// @vitest-environment node

/**
 * Built-output / shell-render assertion: prerendered lexicon pages must keep
 * the inline etymology-anchor click handler (follow-up from #5329 — route-parity
 * strips scripts, so this gate covers them explicitly).
 */

import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import reactRenderer from "@astrojs/react/server.js";
import { experimental_AstroContainer as AstroContainer } from "astro/container";
import { beforeAll, describe, expect, test } from "vitest";
import type { EntryRecord } from "@site/src/lib/lexicon/atlas-data-source";
import { articleProps } from "../helpers/word-atlas-record";

type AstroComponent = Parameters<AstroContainer["renderToString"]>[0];

const ETY_HANDLER_MARKERS = [
  // The inline script must exist and be wired to click on etymology stages.
  "<script",
  "addEventListener('click'",
  // Root scope + selector contract.
  "[data-word-atlas]",
  "[data-ety-note]",
  "[data-ety-note-output]",
  // Output-target traversal contract.
  "closest('.atlas-section')",
  // Active-state + content swap contract.
  "classList.remove('active')",
  "classList.add('active')",
  "dataset.etyNote",
] as const;

const stubRecord = articleProps({
  lemma: "прапор",
  url_slug: "прапор",
  gloss: "flag",
  entry_type: "lemma",
  pos: "noun",
  ipa: null,
  primary_source: "fixture",
  course_usage: [],
}).record as EntryRecord;

describe("etymology inline handler on prerendered lexicon pages", () => {
  let container: AstroContainer;
  let WordAtlasPageShell: AstroComponent;

  beforeAll(async () => {
    const mod = await import("@site/src/lexicon/WordAtlasPageShell.astro");
    WordAtlasPageShell = mod.default as AstroComponent;
    container = await AstroContainer.create();
    container.addServerRenderer({ renderer: reactRenderer });
  });

  test("WordAtlasPageShell ready state embeds the etymology click handler script", async () => {
    const html = await container.renderToString(WordAtlasPageShell, {
      props: {
        state: {
          status: "ready",
          record: stubRecord,
          generatedAt: "test",
          manifestVersion: "0.1",
        },
      },
    });
    for (const marker of ETY_HANDLER_MARKERS) {
      expect(html, `missing marker ${marker}`).toContain(marker);
    }
  });

  test("built dist lexicon HTML keeps the etymology handler when dist/ is present", () => {
    const distLexicon = resolve(process.cwd(), "dist/lexicon");
    if (!existsSync(distLexicon)) {
      // Hermetic unit runs without a prior build still cover the shell render above.
      expect(true).toBe(true);
      return;
    }
    const articleDirs = readdirSync(distLexicon, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name)
      .filter((name) => !["browse", "practice"].includes(name) && !name.startsWith("."));
    expect(articleDirs.length).toBeGreaterThan(0);
    let checked = 0;
    for (const name of articleDirs.slice(0, 5)) {
      const indexPath = join(distLexicon, name, "index.html");
      if (!existsSync(indexPath)) continue;
      const html = readFileSync(indexPath, "utf8");
      for (const marker of ETY_HANDLER_MARKERS) {
        expect(html, `${name} missing ${marker}`).toContain(marker);
      }
      checked += 1;
    }
    expect(checked).toBeGreaterThan(0);
  });
});
