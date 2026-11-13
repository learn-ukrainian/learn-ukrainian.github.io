// @vitest-environment node
/**
 * #12984 — site search and chrome promises.
 *
 * Defect classes: site search reads only a truncated slice of the Word Atlas,
 * the site chrome has no route to /search/, and the search empty state points
 * at the retired /etymology/ page.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterAll, describe, expect, test } from "vitest";
import { experimental_AstroContainer as AstroContainer } from "astro/container";
import { Window } from "happy-dom";
import CourseLayout from "../../layouts/CourseLayout.astro";
import { CHROME_STRINGS } from "../../lib/i18n/chrome";
import {
  buildSearchRowsByShard,
  searchShardForQuery,
  type SearchRow,
  type SearchShardManifest,
} from "../../lib/lexicon/search";
import { atlasItems, createAtlasRowLoader } from "../../lib/site-search";

const root = process.cwd();
const readJson = <T>(path: string): T => JSON.parse(readFileSync(resolve(root, path), "utf8")) as T;

describe("site search finds Word Atlas entries beyond any truncated slice", () => {
  const manifest = readJson<SearchShardManifest>("src/data/lexicon-search-shards.json");
  const rows = readJson<SearchRow[]>("src/data/lexicon-search-index.json");
  const shardRows = buildSearchRowsByShard(manifest, rows);
  const shardByPath = new Map(
    Object.entries(manifest.shards).map(([key, meta]) => [meta.path, shardRows.get(key) ?? []]),
  );
  shardByPath.set(manifest.fullIndex.path, rows);
  const recordingLoader = () => {
    const requested: string[] = [];
    const load = createAtlasRowLoader(async (path: string) => {
      requested.push(path);
      const body = path === "/lexicon/search-shards.json" ? manifest : shardByPath.get(path);
      return { ok: body !== undefined, status: body === undefined ? 404 : 200, json: async () => body };
    });
    return { load, requested };
  };

  const hrefs = async (load: (query: string) => Promise<SearchRow[]>, query: string) =>
    atlasItems(await load(query), query).map((item) => item.href);
  const articleHref = (row: SearchRow) => `/lexicon/${encodeURIComponent(row.s)}/`;

  test("lemmas anywhere in the index and their romanization resolve from one prefix shard", async () => {
    const { load, requested } = recordingLoader();
    const lastSharded = rows.filter((row) => searchShardForQuery(manifest, row.l)).at(-1)!;
    expect(await hrefs(load, lastSharded.l)).toContain(articleHref(lastSharded));

    const ofis = rows.find((row) => row.l === "офіс");
    expect(ofis, "the issue's reproduction lemma is an approved Atlas article").toBeDefined();
    expect((await hrefs(load, "офіс"))[0]).toBe(articleHref(ofis!));
    expect((await hrefs(load, "ofis"))[0]).toBe(articleHref(ofis!));

    expect(requested).not.toContain(manifest.fullIndex.path);
    expect(requested.filter((path) => path === "/lexicon/search-shards.json")).toHaveLength(1);
  });

  test("a query with no prefix shard falls back to the full index, like the Atlas typeahead", async () => {
    const { load, requested } = recordingLoader();
    const unsharded = rows.find((row) => !searchShardForQuery(manifest, row.l));
    expect(unsharded, "the index has a head whose first character has no shard").toBeDefined();
    expect(await hrefs(load, unsharded!.l)).toContain(articleHref(unsharded!));
    expect(requested).toContain(manifest.fullIndex.path);
  });
});

describe("site chrome links to search", () => {
  const windows: Window[] = [];
  afterAll(async () => {
    await Promise.all(windows.map((window) => window.happyDOM.abort()));
  });

  test("the header controls, phone menu and footer link to /search/", async () => {
    const container = await AstroContainer.create();
    const window = new Window();
    windows.push(window);
    window.document.write(
      await container.renderToString(CourseLayout as any, { props: { title: "Course", currentPath: "/b1/" } }),
    );
    const document = window.document;
    for (const selector of ["header .lu-header-controls", 'header nav[aria-label="Mobile primary"]', "footer.lu-footer"]) {
      const link = document.querySelector(`${selector} a[href="/search/"]`);
      expect(link, selector).not.toBeNull();
      expect(link?.querySelector('[data-loc="en"]')?.textContent).toBe(CHROME_STRINGS.en["nav.search"]);
      expect(link?.querySelector('[data-loc="uk"]')?.textContent).toBe(CHROME_STRINGS.uk["nav.search"]);
    }
  });
});

test("search empty state no longer points to the retired Etymology page", () => {
  expect(CHROME_STRINGS.en["search.emptyBody"]).not.toMatch(/etymolog/i);
  expect(CHROME_STRINGS.uk["search.emptyBody"]).not.toMatch(/етимолог/i);
});
