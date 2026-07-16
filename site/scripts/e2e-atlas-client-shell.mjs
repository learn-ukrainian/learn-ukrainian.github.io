#!/usr/bin/env node
/**
 * Deploy-realistic E2E for the atlas 404 client shell (PR3 R4).
 *
 * 1. Expects `site/dist/` from `npm run build`
 * 2. Vendors the F006 fixture runtime tree at `dist/atlas/` (slice 3 owns real deploy vendoring)
 * 3. Serves with true HTTP 404 → 404.html (not astro preview)
 * 4. Asserts: fixture tail slug renders via shell; prerendered slug has no shell boot;
 *    trailing-slash + Cyrillic-encoded slugs work.
 *
 * Usage (from site/):
 *   node ./scripts/e2e-atlas-client-shell.mjs
 */

import { cpSync, existsSync, readdirSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { createGhPages404Server } from "./serve-gh-pages-404.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SITE = resolve(__dirname, "..");
const REPO = resolve(SITE, "..");
const DIST = resolve(SITE, "dist");
const FIXTURE_ATLAS = resolve(REPO, "tests/fixtures/atlas/runtime-tree/atlas");
const DIST_ATLAS = resolve(DIST, "atlas");

const TAIL_SLUG = "fixture-expression";
const TAIL_LEMMA = "на добраніч";

function fail(msg) {
  console.error(`FAIL: ${msg}`);
  process.exitCode = 1;
}

function ok(msg) {
  console.log(`OK: ${msg}`);
}

function pickPrerenderedSlug() {
  const candidates = ["прапор", "кава", "дім", "я", "іван", "вид"];
  for (const slug of candidates) {
    if (existsSync(resolve(DIST, "lexicon", slug, "index.html"))) return slug;
  }
  for (const ent of readdirSync(resolve(DIST, "lexicon"), { withFileTypes: true })) {
    if (!ent.isDirectory()) continue;
    if (["browse", "practice"].includes(ent.name)) continue;
    if (existsSync(resolve(DIST, "lexicon", ent.name, "index.html"))) return ent.name;
  }
  return null;
}

async function main() {
  if (!existsSync(resolve(DIST, "404.html"))) {
    fail("site/dist/404.html missing — run `npm run build` first");
    return;
  }
  if (!existsSync(FIXTURE_ATLAS)) {
    fail(`fixture atlas tree missing: ${FIXTURE_ATLAS}`);
    return;
  }

  rmSync(DIST_ATLAS, { recursive: true, force: true });
  cpSync(FIXTURE_ATLAS, DIST_ATLAS, { recursive: true });
  ok(`vendored fixture atlas → ${DIST_ATLAS}`);

  const prerendered = pickPrerenderedSlug();
  if (!prerendered) {
    fail("no prerendered lexicon article found under dist/lexicon/");
    return;
  }
  ok(`prerendered slug: ${prerendered}`);

  if (existsSync(resolve(DIST, "lexicon", TAIL_SLUG, "index.html"))) {
    fail(`tail slug ${TAIL_SLUG} is unexpectedly prerendered`);
    return;
  }
  ok(`tail slug ${TAIL_SLUG} is not prerendered (will hit 404 shell)`);

  const server = createGhPages404Server({ root: DIST, host: "127.0.0.1", port: 4177 });
  const { baseUrl } = await server.listen();
  ok(`server ${baseUrl}`);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (err) => errors.push(String(err)));

  try {
    const statusProbe = await page.request.get(`${baseUrl}/lexicon/${TAIL_SLUG}/`);
    if (statusProbe.status() !== 404) {
      fail(`expected HTTP 404 for tail slug, got ${statusProbe.status()}`);
    } else {
      ok(`HTTP 404 for /lexicon/${TAIL_SLUG}/`);
    }

    await page.goto(`${baseUrl}/lexicon/${TAIL_SLUG}/`, { waitUntil: "networkidle" });
    await page.waitForSelector("[data-word-atlas]", { timeout: 20_000 });
    const articleText = await page.locator("[data-word-atlas]").innerText();
    if (!articleText.includes(TAIL_LEMMA) && !articleText.includes(TAIL_SLUG)) {
      fail(`tail article missing lemma/slug; got snippet: ${articleText.slice(0, 200)}`);
    } else {
      ok("tail slug rendered article via shell (lemma/slug present)");
    }
    const genericHidden = await page.locator("[data-generic-404][hidden]").count();
    if (genericHidden < 1) {
      fail("generic 404 section should be hidden on lexicon shell path");
    } else {
      ok("generic 404 hidden while shell active");
    }
    const clientWrapped = await page.locator("[data-atlas-client-article]").count();
    if (clientWrapped < 1) {
      fail("expected [data-atlas-client-article] wrapper from client shell");
    } else {
      ok("client shell article wrapper present");
    }

    // Encoded Cyrillic of a fixture slug that is also commonly prerendered
    const encoded = encodeURIComponent("прапор");
    const praporPrerendered = existsSync(resolve(DIST, "lexicon", "прапор", "index.html"));
    await page.goto(`${baseUrl}/lexicon/${encoded}/`, { waitUntil: "networkidle" });
    await page.waitForSelector("[data-word-atlas]", { timeout: 15_000 });
    if (praporPrerendered) {
      const hasClientShellAttr = await page.locator("[data-atlas-client-article]").count();
      if (hasClientShellAttr > 0) {
        fail("prerendered /lexicon/прапор/ unexpectedly mounted client shell article wrapper");
      } else {
        ok("encoded Cyrillic prerendered slug serves static HTML (no client article wrapper)");
      }
    } else {
      ok("encoded Cyrillic slug rendered via shell");
    }

    // No trailing slash → still resolves (server index fallback or shell)
    await page.goto(`${baseUrl}/lexicon/${TAIL_SLUG}`, { waitUntil: "networkidle" });
    await page.waitForSelector("[data-word-atlas]", { timeout: 20_000 });
    ok("tail slug without trailing slash still renders article");

    const preStatus = await page.request.get(`${baseUrl}/lexicon/${prerendered}/`);
    if (preStatus.status() !== 200) {
      fail(`prerendered slug expected 200, got ${preStatus.status()}`);
    } else {
      ok(`HTTP 200 for prerendered /lexicon/${prerendered}/`);
    }
    await page.goto(`${baseUrl}/lexicon/${prerendered}/`, { waitUntil: "networkidle" });
    await page.waitForSelector("[data-word-atlas]", { timeout: 10_000 });
    const clientArticle = await page.locator("[data-atlas-client-article]").count();
    const atlasShellPending = await page.evaluate(
      () => document.documentElement.dataset.atlasShell || "",
    );
    if (clientArticle > 0 || atlasShellPending === "active" || atlasShellPending === "pending") {
      fail(
        `prerendered page should not boot atlas shell (clientArticle=${clientArticle}, dataset=${atlasShellPending})`,
      );
    } else {
      ok("prerendered page has no atlas shell boot");
    }

    await page.goto(`${baseUrl}/this-route-does-not-exist-xyz/`, { waitUntil: "networkidle" });
    const genericVisible = await page.locator("[data-generic-404]:not([hidden])").count();
    if (genericVisible < 1) {
      fail("generic 404 should remain visible for non-lexicon paths");
    } else {
      ok("non-lexicon 404 keeps generic recovery UI");
    }

    if (errors.length) {
      fail(`page errors: ${errors.join(" | ")}`);
    }
  } finally {
    await browser.close();
    await server.close();
  }

  if (process.exitCode && process.exitCode !== 0) {
    console.error("\nE2E FAILED");
  } else {
    console.log("\nE2E PASSED");
  }
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
