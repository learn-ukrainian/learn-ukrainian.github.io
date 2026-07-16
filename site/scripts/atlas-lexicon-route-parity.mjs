#!/usr/bin/env node
/**
 * Build-both-and-diff gate for Atlas scale-out PR #2.
 *
 * Builds merge-base/main and PR-head lexicon article routes against the SAME
 * absolute fixture DB, then byte-compares every selected dist HTML page.
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
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "../..");
const FIXTURE_DB = resolve(REPO_ROOT, "tests/fixtures/atlas/runtime_shards_fixture.db");
const MISSING_SENTINEL = "fixture-missing-sentinel";

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

  // Copy the site tree but skip heavy/generated dirs; node_modules is symlinked.
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

  // Keep only the lexicon article route.
  rmSync(join(siteDir, "src/pages"), { recursive: true, force: true });
  mkdirSync(join(siteDir, "src/pages/lexicon"), { recursive: true });
  cpSync(
    join(lemmaFilesFrom, "src/pages/lexicon/[lemma].astro"),
    join(siteDir, "src/pages/lexicon/[lemma].astro"),
  );
  // Head/main article + shell must come from the same tree as the route.
  for (const rel of [
    "src/lexicon/WordAtlasArticle.astro",
    "src/lexicon/WordAtlasPageShell.astro",
    "src/lib/lexicon/sqlite-atlas-data-source.ts",
    "src/lib/lexicon/atlas-data-source.ts",
    "src/lib/lexicon/word-atlas-page-state.ts",
    "src/lib/lexicon/atlasDb.ts",
  ]) {
    const from = join(lemmaFilesFrom, rel);
    const to = join(siteDir, rel);
    if (existsSync(from)) {
      mkdirSync(dirname(to), { recursive: true });
      cpSync(from, to);
    } else if (existsSync(to) && rel.includes("WordAtlasPageShell")) {
      rmSync(to, { force: true });
    }
  }

  // Ensure hydrated JSON stubs exist for any leftover imports under lib.
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
      writeFileSync(dest, fallback);
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

function main() {
  if (!existsSync(FIXTURE_DB)) {
    throw new Error(`missing fixture DB: ${FIXTURE_DB}`);
  }
  assertFixtureTypeCoverage();

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

    // Share identical practice indexes (empty) so practice visibility matches.
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

    let differing = 0;
    for (const slug of FIXTURE_SLUGS) {
      if (!mainPages.has(slug) || !headPages.has(slug)) {
        throw new Error(`fixture slug missing from build output: ${slug}`);
      }
      const mainBuf = readFileSync(mainPages.get(slug));
      const headBuf = readFileSync(headPages.get(slug));
      const mainHash = sha256(mainBuf);
      const headHash = sha256(headBuf);
      if (mainHash !== headHash) {
        differing += 1;
        console.error(unifiedDiff(mainBuf.toString("utf-8"), headBuf.toString("utf-8"), slug));
        console.error(`PARITY FAIL ${slug} main=${mainHash} head=${headHash}`);
      } else {
        console.log(`PARITY OK ${slug} sha256=${mainHash}`);
      }
    }

    if (differing !== 0) {
      throw new Error(`byte parity failed: differing=${differing}`);
    }
    console.log(
      `atlas lexicon route parity: fixtures=${FIXTURE_SLUGS.length} differing=0 (zero differing files)`,
    );
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
}

main();
