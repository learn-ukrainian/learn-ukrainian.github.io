/**
 * R7 overflow escape hook: PUBLIC_ATLAS_ASSET_BASE_URL / assetBaseUrl override.
 * Design-in only — proves resolve + HttpAtlasDataSource honor the override.
 */
import { describe, expect, test } from "vitest";
import {
  DEFAULT_ATLAS_ASSET_BASE_URL,
  HttpAtlasDataSource,
  resolveAtlasAssetBaseUrl,
  type AtlasFetch,
} from "@site/src/lib/lexicon/http-atlas-data-source";

describe("resolveAtlasAssetBaseUrl (R7 overflow hook)", () => {
  test("defaults to same-origin /atlas when nothing is set", () => {
    expect(resolveAtlasAssetBaseUrl({ env: {} })).toBe(DEFAULT_ATLAS_ASSET_BASE_URL);
    expect(DEFAULT_ATLAS_ASSET_BASE_URL).toBe("/atlas");
  });

  test("honors immutable raw.githubusercontent.com commit-SHA override via env", () => {
    const overflow =
      "https://raw.githubusercontent.com/learn-ukrainian/learn-ukrainian.github.io/0123456789abcdef0123456789abcdef01234567/atlas";
    expect(
      resolveAtlasAssetBaseUrl({
        env: { PUBLIC_ATLAS_ASSET_BASE_URL: overflow },
      }),
    ).toBe(overflow);
  });

  test("explicit assetBaseUrl wins over env", () => {
    expect(
      resolveAtlasAssetBaseUrl({
        assetBaseUrl: "/atlas",
        env: {
          PUBLIC_ATLAS_ASSET_BASE_URL:
            "https://raw.githubusercontent.com/org/repo/deadbeef/atlas",
        },
      }),
    ).toBe("/atlas");
  });

  test("strips trailing slash from override", () => {
    expect(
      resolveAtlasAssetBaseUrl({
        env: {
          PUBLIC_ATLAS_ASSET_BASE_URL:
            "https://raw.githubusercontent.com/org/repo/abc123def456/atlas/",
        },
      }),
    ).toBe("https://raw.githubusercontent.com/org/repo/abc123def456/atlas");
  });
});

describe("HttpAtlasDataSource assetBaseUrl env override smoke", () => {
  test("constructor env override prefixes fetch URLs (overflow path)", async () => {
    const overflow =
      "https://raw.githubusercontent.com/learn-ukrainian/learn-ukrainian.github.io/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/atlas";
    const seen: string[] = [];
    const fetchBytes: AtlasFetch = async (url) => {
      seen.push(url);
      // Minimal valid current.json so resolveSession gets past the first fetch.
      const body = new TextEncoder().encode(
        JSON.stringify({
          schema: "atlas-current",
          schemaVersion: 1,
          dataVersion: "v-test",
          generatedAt: "2026-07-17T00:00:00+00:00",
          manifestUrl: "versions/v-test/manifest.json",
        }),
      );
      return body;
    };

    const source = new HttpAtlasDataSource(fetchBytes, {
      env: { PUBLIC_ATLAS_ASSET_BASE_URL: overflow },
      pointerTtlMs: 0,
      // Force decompress not to run — getEntry will fail later; we only need pointer fetch.
      decompress: (data) => data,
    });

    // getEntry triggers current.json fetch with the overflow base.
    await expect(source.getEntry("test-slug")).rejects.toThrow();
    expect(seen.length).toBeGreaterThanOrEqual(1);
    expect(seen[0]).toBe(`${overflow}/current.json`);
  });
});
