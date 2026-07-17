// @vitest-environment happy-dom

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { afterEach, describe, expect, test } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createElement } from "react";
import {
  createFileAtlasFetch,
  createNodeHttpAtlasDataSource,
} from "@site/src/lib/lexicon/http-atlas-node";
import { parseLexiconArticleSlug } from "@site/src/lib/lexicon/atlas-lexicon-path";
import {
  analyticsClassForState,
  loadAtlasClientShellEntry,
} from "@site/src/lib/lexicon/word-atlas-client-shell";
import { reportAtlasShellAnalytics } from "@site/src/lib/lexicon/atlas-shell-analytics";
import { AtlasDataSourceError } from "@site/src/lib/lexicon/atlas-data-source";
import WordAtlasClientShell from "@site/src/lexicon/WordAtlasClientShell";

const fixtureRuntimeTree = resolve(
  process.cwd(),
  "../tests/fixtures/atlas/runtime-tree",
);
const assetRoot = resolve(fixtureRuntimeTree, "atlas");

function fixtureHttpSource() {
  // File fetch already roots at runtime-tree/atlas/; leave assetBaseUrl empty
  // so HttpAtlasDataSource requests `current.json` not `atlas/current.json`.
  return createNodeHttpAtlasDataSource(createFileAtlasFetch(fixtureRuntimeTree), {
    pointerTtlMs: 0,
  });
}

/** Browser-shaped fetch over the committed F006 fixture tree. */
function fixtureFetchImpl(overrides?: {
  corruptShard?: boolean;
  failUrls?: RegExp;
  failOnceUrls?: RegExp;
}): typeof fetch {
  let failOnceTripped = false;
  return (async (input: RequestInfo | URL) => {
    const url = String(input);
    const path = url.replace(/^https?:\/\/[^/]+/, "");
    if (overrides?.failUrls?.test(path)) {
      throw new TypeError(`network down: ${path}`);
    }
    if (overrides?.failOnceUrls?.test(path) && !failOnceTripped) {
      failOnceTripped = true;
      throw new TypeError(`transient network: ${path}`);
    }
    const relative = path.replace(/^\/atlas\//, "");
    const filePath = resolve(assetRoot, relative);
    let body: Buffer;
    try {
      body = readFileSync(filePath);
    } catch {
      return new Response("missing", { status: 404 });
    }
    if (overrides?.corruptShard && relative.includes("/entries/") && relative.endsWith(".json.gz")) {
      // Truncate so gunzip / integrity checks fail.
      body = body.subarray(0, Math.min(32, body.length));
    }
    return new Response(new Uint8Array(body), {
      status: 200,
      headers: { "content-type": "application/octet-stream" },
    });
  }) as typeof fetch;
}

afterEach(() => {
  cleanup();
  document.title = "";
  delete document.documentElement.dataset.atlasShell;
});

describe("parseLexiconArticleSlug", () => {
  test("matches trailing-slash and Cyrillic-encoded forms", () => {
    expect(parseLexiconArticleSlug("/lexicon/прапор/")).toBe("прапор");
    expect(parseLexiconArticleSlug("/lexicon/%D0%BF%D1%80%D0%B0%D0%BF%D0%BE%D1%80/")).toBe(
      "прапор",
    );
    expect(parseLexiconArticleSlug("/lexicon/прапор")).toBe("прапор");
    expect(parseLexiconArticleSlug("/base/lexicon/прапор/", "/base/")).toBe("прапор");
  });

  test("rejects non-article lexicon paths", () => {
    expect(parseLexiconArticleSlug("/lexicon/")).toBeNull();
    expect(parseLexiconArticleSlug("/lexicon/browse/")).toBe("browse"); // article-shaped; real browse is prerendered
    expect(parseLexiconArticleSlug("/a1/")).toBeNull();
    expect(parseLexiconArticleSlug("/404/")).toBeNull();
  });
});

describe("loadAtlasClientShellEntry (fixture tree)", () => {
  test("loading→ready for a known fixture slug", async () => {
    const source = fixtureHttpSource();
    const state = await loadAtlasClientShellEntry("прапор", source);
    expect(state.status).toBe("ready");
    if (state.status === "ready") {
      expect(state.record.entry.lemma).toBe("прапор");
      expect(analyticsClassForState(state)).toBe("atlas_tail_rendered");
    }
  });

  test("not_found for an unknown slug", async () => {
    const source = fixtureHttpSource();
    const state = await loadAtlasClientShellEntry("немає-такого-слова-xyz", source);
    expect(state).toEqual({ status: "not_found", slug: "немає-такого-слова-xyz" });
    expect(analyticsClassForState(state)).toBe("atlas_not_found");
  });

  test("corrupt when shard integrity fails", async () => {
    const fetchBytes = createFileAtlasFetch(fixtureRuntimeTree);
    const wrapping: typeof fetchBytes = async (url) => {
      const bytes = await fetchBytes(url);
      if (url.includes("/entries/") && url.endsWith(".json.gz")) {
        return bytes.subarray(0, 24);
      }
      return bytes;
    };
    const source = createNodeHttpAtlasDataSource(wrapping, {
      pointerTtlMs: 0,
    });
    const state = await loadAtlasClientShellEntry("прапор", source);
    expect(state.status).toBe("corrupt");
    expect(analyticsClassForState(state)).toBe("atlas_fetch_failed");
  });

  test("network_error maps unavailable failures", async () => {
    const source = {
      async getEntry() {
        throw new AtlasDataSourceError("unavailable", "offline");
      },
      async search() {
        throw new Error("unused");
      },
      async getDeck() {
        throw new Error("unused");
      },
    };
    const state = await loadAtlasClientShellEntry("прапор", source);
    expect(state.status).toBe("network_error");
    expect(analyticsClassForState(state)).toBe("atlas_fetch_failed");
  });
});

describe("reportAtlasShellAnalytics", () => {
  test("success overrides path+title once and emits classification event", () => {
    const calls: unknown[] = [];
    reportAtlasShellAnalytics({
      classification: "atlas_tail_rendered",
      slug: "прапор",
      lemma: "прапор",
      goatcounter: {
        count: (vars) => {
          calls.push(vars);
        },
      },
    });
    expect(document.title).toContain("прапор");
    expect(calls).toEqual([
      { path: "/lexicon/прапор/", title: "прапор" },
      { path: "atlas_tail_rendered", title: "прапор", event: true },
    ]);
  });

  test("failures emit classification event only", () => {
    const calls: unknown[] = [];
    reportAtlasShellAnalytics({
      classification: "atlas_not_found",
      slug: "немає",
      goatcounter: {
        count: (vars) => {
          calls.push(vars);
        },
      },
    });
    expect(calls).toEqual([{ path: "atlas_not_found", title: "немає", event: true }]);
  });
});

describe("WordAtlasClientShell React mount", () => {
  test("renders fixture article via stubbed fetch", async () => {
    render(
      createElement(WordAtlasClientShell, {
        pathname: "/lexicon/прапор/",
        assetBaseUrl: "/atlas",
        fetchImpl: fixtureFetchImpl(),
      }),
    );
    expect(screen.getByRole("status")).toHaveAttribute("data-word-atlas-state", "loading");
    await waitFor(() => {
      expect(document.querySelector("[data-word-atlas]")).toBeTruthy();
    });
    expect(document.body.textContent).toContain("прапор");
  });

  test("shows слово не знайдено for missing slug", async () => {
    render(
      createElement(WordAtlasClientShell, {
        pathname: "/lexicon/немає-такого-xyz/",
        assetBaseUrl: "/atlas",
        fetchImpl: fixtureFetchImpl(),
      }),
    );
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveAttribute("data-word-atlas-state", "not_found");
    });
    expect(screen.getByRole("heading", { level: 1 }).textContent).toMatch(/Слово не знайдено/i);
  });

  test("shows corrupt state for truncated shard", async () => {
    render(
      createElement(WordAtlasClientShell, {
        pathname: "/lexicon/прапор/",
        assetBaseUrl: "/atlas",
        fetchImpl: fixtureFetchImpl({ corruptShard: true }),
      }),
    );
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveAttribute("data-word-atlas-state", "corrupt");
    });
    expect(screen.getByRole("heading", { level: 1 }).textContent).toMatch(/пошкоджен/i);
  });

  test("network fail → retry recovers", async () => {
    const user = userEvent.setup();
    render(
      createElement(WordAtlasClientShell, {
        pathname: "/lexicon/прапор/",
        assetBaseUrl: "/atlas",
        fetchImpl: fixtureFetchImpl({ failOnceUrls: /current\.json$/ }),
      }),
    );
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveAttribute("data-word-atlas-state", "network_error");
    });
    await user.click(screen.getByRole("button", { name: /Спробувати знову/i }));
    await waitFor(() => {
      expect(document.querySelector("[data-word-atlas]")).toBeTruthy();
    });
  });

  test("not_found via search-index preflight never requests current.json", async () => {
    const requested: string[] = [];
    const fetchImpl = (async (input: RequestInfo | URL) => {
      const url = String(input);
      requested.push(url);
      if (url.includes("search-index.json")) {
        return new Response(JSON.stringify([{ l: "прапор", s: "прапор", g: "flag" }]), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }
      return new Response("should-not-fetch", { status: 500 });
    }) as typeof fetch;

    render(
      createElement(WordAtlasClientShell, {
        pathname: "/lexicon/неіснуючесловоxyzqqq/",
        assetBaseUrl: "/atlas",
        fetchImpl,
      }),
    );
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveAttribute("data-word-atlas-state", "not_found");
    });
    expect(screen.getByRole("heading", { level: 1 }).textContent).toMatch(/Word not found|Слово не знайдено/);
    expect(requested.some((url) => url.includes("current.json"))).toBe(false);
    expect(requested.some((url) => url.includes("search-index.json"))).toBe(true);
  });
});
