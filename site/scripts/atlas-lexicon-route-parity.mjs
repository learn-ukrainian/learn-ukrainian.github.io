#!/usr/bin/env node
/**
 * Build-both-and-diff gate for Atlas lexicon routes (PR2 → PR3 adapted).
 *
 * Builds merge-base/main and PR-head lexicon article routes against the SAME
 * absolute fixture DB, then:
 *   - NORMALIZED-DOM compares the `[data-word-atlas]` article region
 *     (Astro→React port cannot stay byte-identical — CSS-module hashes,
 *     attribute order, whitespace)
 *   - BYTE-compares everything OUTSIDE the article region (scripts stripped)
 *
 * Usage (from repo root):
 *   node --experimental-strip-types site/scripts/atlas-lexicon-route-parity.mjs
 */

import { createHash } from "node:crypto";
import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { Window } from "happy-dom";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "../..");
const FIXTURE_DB = resolve(REPO_ROOT, "tests/fixtures/atlas/runtime_shards_fixture.db");
const MISSING_SENTINEL = "fixture-missing-sentinel";
const SITE = resolve(REPO_ROOT, "site");

/** Named parity scenarios + every ATLAS_ENTRY_TYPES synthetic + form_route. */
const FIXTURE_SLUGS = [
  "прапор",
  "файний",
  "будь-ласка",
  "доконаний-вид",
  "іване",
  "fixture-expression",
  "fixture-phraseologism",
  "fixture-proverb",
  "fixture-proper-name",
  "ілля",
];

const REQUIRED_TYPES = [
  "lemma",
  "expression",
  "phraseologism",
  "proverb",
  "multiword_term",
  "proper_name",
  "form_route",
];

function sha256(buf) {
  return createHash("sha256").update(buf).digest("hex");
}

function run(cmd, args, opts = {}) {
  const result = spawnSync(cmd, args, {
    encoding: "utf-8",
    maxBuffer: 50 * 1024 * 1024,
    ...opts,
  });
  if (result.status !== 0) {
    const detail = [result.stdout, result.stderr].filter(Boolean).join("\n");
    throw new Error(`${cmd} ${args.join(" ")} failed (${result.status}):\n${detail.slice(-4000)}`);
  }
  return result;
}

function assertFixtureTypeCoverage() {
  const require = createRequire(import.meta.url);
  const Database = require("better-sqlite3");
  const db = new Database(FIXTURE_DB, { readonly: true, fileMustExist: true });
  try {
    const present = new Set(
      db
        .prepare(
          `SELECT entry_type AS t FROM articles
           WHERE review_state = 'approved' AND visibility = 'public'`,
        )
        .all()
        .map((row) => row.t),
    );
    const formRoutes = db
      .prepare(
        `SELECT COUNT(*) AS n FROM article_payloads ap
         LEFT JOIN articles a ON a.slug = ap.slug
         WHERE ap.is_public_route = 1 AND a.slug IS NULL`,
      )
      .get().n;
    if (formRoutes > 0) present.add("form_route");
    const missing = REQUIRED_TYPES.filter((t) => !present.has(t));
    if (missing.length) {
      throw new Error(`fixture type-set incomplete: missing=${missing.join(",")}`);
    }
    console.log(
      `fixture type-set coverage: ${REQUIRED_TYPES.join(" ")} (exact required set present)`,
    );
    const sentinel = db
      .prepare(`SELECT 1 AS n FROM article_payloads WHERE slug = ?`)
      .get(MISSING_SENTINEL);
    if (sentinel) {
      throw new Error(`missing sentinel ${MISSING_SENTINEL} must not be a public route`);
    }
  } finally {
    db.close();
  }
}

function emptyContentConfig() {
  return `import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
export const collections = {
  docs: defineCollection({
    loader: glob({ pattern: 'empty/**/*.{md,mdx}', base: './src/content/docs' }),
    schema: z.object({ title: z.string() }).passthrough(),
  }),
  readings: defineCollection({
    loader: glob({ pattern: 'empty/**/*.{md,mdx}', base: './src/content/readings' }),
    schema: z.object({ title: z.string(), genre: z.string() }).passthrough(),
  }),
};
`;
}

function prepareSiteCopy({ label, sourceSite, lemmaFilesFrom, outDir, nodeModulesFrom }) {
  const siteDir = join(outDir, label);
  rmSync(siteDir, { recursive: true, force: true });
  mkdirSync(siteDir, { recursive: true });

  run("rsync", [
    "-a",
    "--delete",
    "--exclude",
    "node_modules",
    "--exclude",
    "dist",
    "--exclude",
    ".astro",
    "--exclude",
    "src/content/docs",
    "--exclude",
    "src/content/readings",
    `${sourceSite}/`,
    `${siteDir}/`,
  ]);

  mkdirSync(join(siteDir, "src/content/docs/empty"), { recursive: true });
  mkdirSync(join(siteDir, "src/content/readings/empty"), { recursive: true });
  writeFileSync(join(siteDir, "src/content.config.ts"), emptyContentConfig());

  rmSync(join(siteDir, "src/pages"), { recursive: true, force: true });
  mkdirSync(join(siteDir, "src/pages/lexicon"), { recursive: true });
  cpSync(
    join(lemmaFilesFrom, "src/pages/lexicon/[lemma].astro"),
    join(siteDir, "src/pages/lexicon/[lemma].astro"),
  );

  // Article + shell + React port deps must come from the same tree as the route.
  for (const rel of [
    "src/lexicon/WordAtlasArticle.astro",
    "src/lexicon/WordAtlasArticle.tsx",
    "src/lexicon/WordAtlasArticle.module.css",
    "src/lexicon/WordAtlasPageShell.astro",
    "src/lexicon/AtlasTypeahead.astro",
    "src/lib/lexicon/sqlite-atlas-data-source.ts",
    "src/lib/lexicon/atlas-data-source.ts",
    "src/lib/lexicon/word-atlas-page-state.ts",
    "src/lib/lexicon/atlasDb.ts",
    "src/lib/lexicon/word-atlas-article-model.ts",
    "src/lib/lexicon/safe-url.ts",
    "src/lib/lexicon/heritage-severity.ts",
    "src/lib/lexicon/register-markers.ts",
    "src/lib/i18n/plural.ts",
    "src/styles/word-atlas.css",
  ]) {
    const from = join(lemmaFilesFrom, rel);
    const to = join(siteDir, rel);
    if (existsSync(from)) {
      mkdirSync(dirname(to), { recursive: true });
      cpSync(from, to);
    } else if (existsSync(to) && (rel.includes("WordAtlasPageShell") || rel.endsWith(".astro"))) {
      // Head may have deleted the Astro article; remove stale copies from rsync base.
      if (rel.includes("WordAtlasArticle.astro")) rmSync(to, { force: true });
    }
  }

  // If head no longer ships the Astro article, ensure the rsynced copy is gone.
  const headAstro = join(lemmaFilesFrom, "src/lexicon/WordAtlasArticle.astro");
  const copyAstro = join(siteDir, "src/lexicon/WordAtlasArticle.astro");
  if (!existsSync(headAstro) && existsSync(copyAstro) && label === "head") {
    rmSync(copyAstro, { force: true });
  }

  const dataDir = join(siteDir, "src/data");
  mkdirSync(dataDir, { recursive: true });
  for (const name of [
    "lexicon-manifest.json",
    "lexicon-search-index.json",
    "lexicon-search-aliases.json",
    "lexicon-search-shards.json",
    "lexicon-daily-pool.json",
    "lexicon-browse-meta.json",
    "lexicon-browse-flagged.json",
    "curriculum-stats.json",
  ]) {
    const dest = join(dataDir, name);
    if (!existsSync(dest)) {
      const fallback =
        name === "lexicon-manifest.json"
          ? JSON.stringify({ version: "0.1", generated_at: "test", entries: [] })
          : name.includes("browse-meta")
            ? JSON.stringify({ total: 0, letterCounts: {}, chipCounts: {} })
            : name.includes("stats")
              ? "{}"
              : "[]";
      try {
        // wx: create-only — closes the existsSync→writeFileSync TOCTOU race.
        writeFileSync(dest, fallback, { flag: "wx" });
      } catch (err) {
        if (err && typeof err === "object" && "code" in err && err.code === "EEXIST") {
          // Another writer created the fixture between existsSync and write.
          continue;
        }
        throw err;
      }
    }
  }

  const nm = nodeModulesFrom;
  if (!existsSync(nm)) {
    throw new Error(`missing node_modules at ${nm}; run npm install in site/`);
  }
  symlinkSync(nm, join(siteDir, "node_modules"));
  return siteDir;
}

function buildLexiconRoutes(siteDir, distName) {
  const distDir = join(siteDir, distName);
  rmSync(distDir, { recursive: true, force: true });
  const env = {
    ...process.env,
    ATLAS_DB_PATH: FIXTURE_DB,
    ATLAS_MANIFEST_ALLOW_STALE_POINTER: "1",
    ASTRO_TELEMETRY_DISABLED: "1",
  };
  run("npx", ["astro", "build", "--outDir", distName], {
    cwd: siteDir,
    env,
    timeout: 300000,
  });
  return distDir;
}

function collectLexiconHtml(distDir) {
  const root = join(distDir, "lexicon");
  const out = new Map();
  if (!existsSync(root)) return out;
  for (const slug of readdirSync(root)) {
    const htmlPath = join(root, slug, "index.html");
    if (existsSync(htmlPath)) out.set(slug, htmlPath);
  }
  return out;
}

async function loadNormalizeHelpers() {
  const mod = await import(
    pathToFileURL(join(SITE, "tests/helpers/normalize-article-dom.ts")).href
  );
  return mod;
}

function installDomGlobals() {
  const window = new Window({ url: "https://example.test/" });
  globalThis.window = window;
  globalThis.document = window.document;
  globalThis.DOMParser = window.DOMParser;
  globalThis.Node = window.Node;
  return window;
}

function unifiedDiff(left, right, label) {
  const leftLines = left.split("\n");
  const rightLines = right.split("\n");
  const lines = [`--- main/${label}`, `+++ head/${label}`];
  const limit = Math.max(leftLines.length, rightLines.length);
  for (let i = 0; i < limit; i += 1) {
    const a = leftLines[i];
    const b = rightLines[i];
    if (a === b) continue;
    if (a !== undefined) lines.push(`-${a}`);
    if (b !== undefined) lines.push(`+${b}`);
    if (lines.length > 80) {
      lines.push("... diff truncated ...");
      break;
    }
  }
  return lines.join("\n");
}

async function main() {
  if (!existsSync(FIXTURE_DB)) {
    throw new Error(`missing fixture DB: ${FIXTURE_DB}`);
  }
  assertFixtureTypeCoverage();
  installDomGlobals();
  const { normalizeArticleDom, extractArticleRegion, stripArticleRegion } =
    await loadNormalizeHelpers();

  const headSite = resolve(REPO_ROOT, "site");
  const mainWorktree = join(tmpdir(), "atlas-pr2-parity-main");
  if (!existsSync(join(mainWorktree, "site"))) {
    rmSync(mainWorktree, { recursive: true, force: true });
    run("git", ["worktree", "add", "--detach", mainWorktree, "origin/main"], {
      cwd: REPO_ROOT,
    });
  } else {
    run("git", ["-C", mainWorktree, "fetch", "origin", "main"], { cwd: REPO_ROOT });
    run("git", ["-C", mainWorktree, "checkout", "--detach", "origin/main"], {
      cwd: REPO_ROOT,
    });
  }

  const scratch = mkdtempSync(join(tmpdir(), "atlas-lexicon-parity-"));
  try {
    const mainSiteCopy = prepareSiteCopy({
      label: "main",
      sourceSite: join(mainWorktree, "site"),
      lemmaFilesFrom: join(mainWorktree, "site"),
      outDir: scratch,
      nodeModulesFrom: join(headSite, "node_modules"),
    });
    const headSiteCopy = prepareSiteCopy({
      label: "head",
      sourceSite: headSite,
      lemmaFilesFrom: headSite,
      outDir: scratch,
      nodeModulesFrom: join(headSite, "node_modules"),
    });

    for (const siteCopy of [mainSiteCopy, headSiteCopy]) {
      for (const rel of ["public/lexicon", "public/api/lexicon"]) {
        const dir = join(siteCopy, rel);
        mkdirSync(dir, { recursive: true });
        for (const level of ["A1", "A2", "B1", "B2", "C1", "C2"]) {
          writeFileSync(
            join(dir, `practice-index.${level}.json`),
            JSON.stringify({ deckVersion: "parity", level, items: [] }),
          );
        }
      }
    }

    console.log(`building main against fixture ${FIXTURE_DB}`);
    const mainDist = buildLexiconRoutes(mainSiteCopy, "dist-parity-main");
    console.log(`building head against fixture ${FIXTURE_DB}`);
    const headDist = buildLexiconRoutes(headSiteCopy, "dist-parity-head");

    const mainPages = collectLexiconHtml(mainDist);
    const headPages = collectLexiconHtml(headDist);

    const mainSet = [...mainPages.keys()].sort();
    const headSet = [...headPages.keys()].sort();
    if (JSON.stringify(mainSet) !== JSON.stringify(headSet)) {
      throw new Error(
        `route-path sets differ:\n main=${JSON.stringify(mainSet)}\n head=${JSON.stringify(headSet)}`,
      );
    }

    for (const side of [mainPages, headPages]) {
      if (side.has(MISSING_SENTINEL)) {
        throw new Error(`missing sentinel ${MISSING_SENTINEL} has a generated page`);
      }
    }

    let articleDiffering = 0;
    let shellDiffering = 0;
    for (const slug of FIXTURE_SLUGS) {
      if (!mainPages.has(slug) || !headPages.has(slug)) {
        throw new Error(`fixture slug missing from build output: ${slug}`);
      }
      const mainHtml = readFileSync(mainPages.get(slug), "utf8");
      const headHtml = readFileSync(headPages.get(slug), "utf8");

      const mainArticle = normalizeArticleDom(extractArticleRegion(mainHtml));
      const headArticle = normalizeArticleDom(extractArticleRegion(headHtml));
      if (mainArticle !== headArticle) {
        articleDiffering += 1;
        console.error(unifiedDiff(mainArticle, headArticle, `${slug}[article-dom]`));
        console.error(`ARTICLE DOM PARITY FAIL ${slug}`);
      } else {
        console.log(`ARTICLE DOM PARITY OK ${slug}`);
      }

      const mainShell = stripArticleRegion(mainHtml);
      const headShell = stripArticleRegion(headHtml);
      const mainHash = sha256(mainShell);
      const headHash = sha256(headShell);
      if (mainHash !== headHash) {
        shellDiffering += 1;
        console.error(unifiedDiff(mainShell, headShell, `${slug}[outside-article]`));
        console.error(`SHELL BYTE PARITY FAIL ${slug} main=${mainHash} head=${headHash}`);
      } else {
        console.log(`SHELL BYTE PARITY OK ${slug} sha256=${mainHash}`);
      }
    }

    if (articleDiffering !== 0 || shellDiffering !== 0) {
      throw new Error(
        `parity failed: articleDomDiffering=${articleDiffering} shellByteDiffering=${shellDiffering}`,
      );
    }
    console.log(
      `atlas lexicon route parity: fixtures=${FIXTURE_SLUGS.length} articleDomDiffering=0 shellByteDiffering=0`,
    );
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
