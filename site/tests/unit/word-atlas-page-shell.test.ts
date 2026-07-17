// @vitest-environment node

import reactRenderer from "@astrojs/react/server.js";
import { experimental_AstroContainer as AstroContainer } from "astro/container";
import { beforeAll, describe, expect, test } from "vitest";
import type { EntryRecord } from "@site/src/lib/lexicon/atlas-data-source";
import type { WordAtlasPageState } from "@site/src/lib/lexicon/word-atlas-page-state";
import { articleProps } from "../helpers/word-atlas-record";

type AstroComponent = Parameters<AstroContainer["renderToString"]>[0];

const stubRecord = articleProps({
  lemma: "прапор",
  url_slug: "прапор",
  gloss: "flag",
  entry_type: "lemma",
  pos: "noun",
  ipa: null,
  primary_source: "fixture",
  course_usage: [],
}).record;

describe("WordAtlasPageShell dormant states", () => {
  let container: AstroContainer;
  let WordAtlasPageShell: AstroComponent;

  beforeAll(async () => {
    ({ default: WordAtlasPageShell } = await import(
      "@site/src/lexicon/WordAtlasPageShell.astro"
    ));
    container = await AstroContainer.create();
    container.addServerRenderer({ renderer: reactRenderer });
  });

  async function render(state: WordAtlasPageState): Promise<string> {
    return container.renderToString(WordAtlasPageShell, { props: { state } });
  }

  test("ready delegates to the article with no extra shell wrapper DOM", async () => {
    const html = await render({
      status: "ready",
      record: stubRecord as EntryRecord,
      generatedAt: "test",
      manifestVersion: "0.1",
    });
    expect(html).toContain("data-word-atlas");
    expect(html).not.toContain("data-word-atlas-state=");
    expect(html).toContain("прапор");
  });

  test("loading exposes aria-busy without article markup", async () => {
    const html = await render({ status: "loading" });
    expect(html).toContain('aria-busy="true"');
    expect(html).toContain('data-word-atlas-state="loading"');
    expect(html).not.toContain("data-word-atlas=");
  });

  test("missing is a 404 shell with lexicon actions", async () => {
    const html = await render({ status: "missing", slug: "немає" });
    expect(html).toContain('data-http-status="404"');
    expect(html).toContain("немає");
    expect(html).toContain('href="/lexicon/"');
    expect(html).toContain("Слово не знайдено");
    expect(html).toContain("Word not found");
    expect(html).not.toContain("data-word-atlas=");
  });

  test("offline is a 503 shell and only offers retry when retryable", async () => {
    const retryable = await render({
      status: "offline",
      message: "down",
      retryable: true,
    });
    expect(retryable).toContain('data-http-status="503"');
    expect(retryable).toContain("data-word-atlas-retry");

    const terminal = await render({
      status: "offline",
      message: "corrupt",
      retryable: false,
    });
    expect(terminal).toContain('data-http-status="503"');
    expect(terminal).not.toContain("data-word-atlas-retry");
    expect(terminal).not.toContain("data-word-atlas=");
  });

  test("version-mismatch is a 409 shell that discards partial article data", async () => {
    const html = await render({
      status: "version-mismatch",
      expectedVersion: "sqlite-0.1",
      actualVersion: "sqlite-0.2",
    });
    expect(html).toContain('data-http-status="409"');
    expect(html).toContain("sqlite-0.1");
    expect(html).toContain("data-word-atlas-retry");
    expect(html).not.toContain("data-word-atlas=");
  });
});
