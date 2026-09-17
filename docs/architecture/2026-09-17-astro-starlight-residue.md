---
title: "Astro truth audit — Starlight/Docusaurus residue classification"
status: active
date: 2026-09-17
owner: Claude / docs-knowledge stream (#5535)
scope: "#5538; evidence report and fix routing only — no renames, no compatibility-path removal"
---

# Astro truth audit — Starlight/Docusaurus residue classification

Issue: [#5538](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5538)
· Stream epic: #5535 · Measured at commit `1f7694e857` (tracked files only, per
the [authority contract](docs-authority-lifecycle.md)).

**This report is not an architecture statement.** The canonical statement stays
[`2026-06-09-ui-astro-without-starlight.md`](2026-06-09-ui-astro-without-starlight.md)
(ACCEPTED). This file classifies what is left over and routes the fixes.

## 1. Verdict on the canonical statement

The decision holds: the learner UI is plain Astro under `site/`, with no
Starlight runtime.

| Truth anchor | Evidence at `1f7694e857` |
| --- | --- |
| No Starlight/Docusaurus dependency | `site/package.json` dependencies: `astro`, `@astrojs/mdx`, `@astrojs/react`, `@astrojs/sitemap`, … — no `@astrojs/starlight*`. `site/package-lock.json` has zero `@astrojs/starlight` entries. |
| No Starlight integration | `site/astro.config.mjs` `integrations`: two local hooks, `mdx()`, `react()`, `sitemap()`. |
| One compatibility alias | `site/astro.config.mjs:80` maps `@astrojs/starlight/components` → `site/src/starlight-compat/index.ts` (local `Tabs` + `TabItem`). |
| Deploy | No `starlight`/`docusaurus` string anywhere under `.github/`. |

Three **evidence bullets** inside the canonical record have drifted. They are
recorded as a dated amendment in that file (authority contract: never silently
edit an accepted record):

1. It names `starlight/astro.config.mjs`. The directory was renamed to `site/`
   on 2026-06-13 (`0e6310ae1a`), and the transitional symlink was dropped the
   same day (`772122da52`). No `starlight` path is tracked today.
2. It says `@astrojs/starlight` "stays in `package.json` (unused)". The
   dependency was removed on 2026-06-08 (`666b6a551f`); it was already absent
   at the record's own commit (`c4eafc943a`).
3. It defers the directory rename as cosmetic. The rename is done.

## 2. Deterministic inventory

Reproduce with `git grep` against the commit, so sparse checkouts and untracked
files cannot change the result:

```bash
SHA=1f7694e857
git grep -Iil starlight  $SHA | wc -l     # files
git grep -Ii  starlight  $SHA | wc -l     # lines
git grep -Iil docusaurus $SHA | wc -l
git grep -Il '@astrojs/starlight/components' $SHA -- site/src/content/docs | wc -l
```

| Token (case-insensitive) | Files | Lines |
| --- | ---: | ---: |
| `starlight` | 680 | 1330 |
| `docusaurus` | 30 | 68 |

`starlight` by top-level path: `site` 412 · `docs` 200 · `curriculum` 41 ·
`scripts` 9 · `tests` 4 · `audit` 3 · root/config files 9 · other 2.
Within `docs/`: `session-state` 86 · `dispatch-briefs` 43 · `architecture` 20 ·
`handoffs` 9 · `best-practices` 9 · root 8 · `research` 6 · `plans` 5 · rest 14.

Secondary tokens that the two words above do not catch (outside generated
content): `--ifm-` (Docusaurus Infima variables) 12 files / 632 lines, `--sl-`
(Starlight variables) 6 / 49, `STARLIGHT_` constants 9 / 20.

Counts are a map, not an argument: frequency is never treated as authority.

## 3. Classification register

Classes follow #5538: **1** stale current documentation · **2** historical
evidence · **3** live compatibility shim · **4** stale command/identifier ·
**5** obsolete test fixture · **6** generated-content contract · **7** uncertain.

### Class 3 — live compatibility shim (keep)

| Reference | Evidence |
| --- | --- |
| `site/astro.config.mjs:80` Vite alias | Resolves the import emitted into every tabbed lesson. |
| `site/src/starlight-compat/{index.ts,Tabs.astro,TabItem.astro}` | The alias target; renders `div.lu-tabs` / `.lu-tab-panel`. |
| `tests/build/upgrade_browser_check.mjs:38` | Mirrors the alias for the upgrade browser check; must change in the same PR as the alias. |
| `--sl-*` variables | Defined in `site/src/styles/course.css` (13) and `site/src/css/custom.css` (1); consumed by `ActivityPlaceholder.tsx`, `LevelLanding.module.css`, `pages/etymology/index.astro`. A local token layer with Starlight names. |
| `--ifm-*` variables | 426 lines across 11 `site/src` files; `custom.css:101` declares them as the "Infima / Docusaurus compatibility shim" for migrated activity CSS. |

The two CSS layers are outside the alias removal gate (§5). Renaming them is a
large mechanical change with visual-regression risk and no functional gain; it
is not routed to any batch here.

### Class 6 — generated-content contract

| Reference | Evidence |
| --- | --- |
| `scripts/generate_mdx/core.py:716` | The only emitter: `import { Tabs, TabItem } from '@astrojs/starlight/components';`. |
| Committed MDX importers | **400 of 422** `.mdx` files under `site/src/content/docs/` (b1 94 · b2 93 · a2 69 · a1-v1 55 · a1 44 · folk 40 · bio 5). Zero import the shim path directly. The issue's "~356" estimate is superseded by this count. |

### Class 4 — stale identifier, behavior-neutral (cosmetic)

| Reference | Note |
| --- | --- |
| `site/package.json:2` `"name": "starlight"` (+ `package-lock.json:2,8`) | Issue seed. Private package; the name is not consumed. |
| `site/astro.config.mjs:21-22,74,79` `starlightRoot` / `starlightNodeModules` | Issue seed. Local constants. |
| `STARLIGHT_DOCS_DIR` — `scripts/paths.py:20`, `scripts/generate_mdx/utils.py:17`, `scripts/validate/validate_mdx.py:25`; `STARLIGHT_DOCS` `generate_mdx_stubs.py:22`; `STARLIGHT_DIR` `scripts/validate/validate_html.py:33`, `site/tests/unit/build-renders.test.ts:21` | All already point at `site/…`. Imported by `scripts/build/prev_next.py`, `scripts/generate_mdx/core.py`; monkeypatched by name in `tests/test_archive_resolution.py:151`. Four parallel definitions of one path is a separate duplication finding. |
| Root `package.json:73-75` `build:starlight`, `build:starlight:full`, `dev:starlight` | Already run `--prefix site`. Tracked callers: `README.md:84`, `docs/SCRIPTS.md:1177`. Same cleanup is recommended in `2026-09-05-astro-7-vs-lighter-ssg.md` item 4. |
| `site/src/components/HashTabSync.tsx:7` `StarlightTabsElement` | Type name only; see U1 for the behavior question on the same file. |
| `pyproject.toml:22` marker text "Docusaurus website integrity tests"; `tests/test_site_links.py:325,395` section headers | Descriptive text. |
| `site/src/css/custom.css:249-282`, `site/src/styles/lesson.css:4-5,349` comments | Describe Starlight's `.sl-container` / `markdown.css`, which no longer load. See U3 for whether the rules under them are dead. |

### Class 4 — stale identifier with a functional effect (not cosmetic)

These reference `starlight/…` or `docusaurus/…` paths that no longer exist, so
the configuration silently does nothing.

| Reference | Effect |
| --- | --- |
| `.dagger/src/learn_ukrainian_ci/main.py:121-123` | `without_directory("starlight/node_modules" / ".astro" / "dist")` is a no-op. The bare `"node_modules"` entry strips only the repo root, and no `site/…` entry exists, so `site/node_modules`, `site/.astro`, `site/dist` are uploaded to Dagger. The surrounding comment names exactly this bloat as the 2026-05-17 disk-fill cause. **Highest-priority follow-up.** |
| `scripts/audit/content_surface_gates.py:113` | Path-leak pattern `\bstarlight/src/…` cannot match a leaked `site/src/…` path in learner-facing content. |
| `.trufflehogignore:5` `^starlight/astro\.config\.mjs$` | Dead path. Its justification ("public Algolia credentials in site config") is also obsolete: `site/astro.config.mjs` contains no Algolia/DocSearch. Remove rather than re-point. |
| `pyproject.toml:37,77` ruff/mypy `exclude = ["starlight/"]` | Dead. Harmless today (`site/` tracks zero `.py` files). |
| `.yamllint:22` `docusaurus/node_modules/` | Dead ignore. |
| `agents_extensions/shared/settings.json:29-31,176-178,865` | Docusaurus read/`cd docusaurus` permissions and a `starlight/src/` path entry. Source for deployed harness copies; mirrored in `docs/CLAUDE-CODE-FEATURES.md:78`. |
| `.gitignore:285,426` comments | Line 285 claims a `starlight` compat symlink is kept. It is neither tracked nor ignored, and `772122da52` dropped it. |
| `scripts/pipeline/module_archetypes.py:34,309` `starlight_current_tabs` / "Current Starlight tabs:" | **Prompt-visible string** (injected as `MODULE_ARCHETYPE` at `scripts/build/linear_pipeline.py:3659`), pinned by `tests/test_module_archetypes.py:68`. Changing it is a prompt change, not a rename. |

### Class 5 — obsolete test fixture

| Reference | Note |
| --- | --- |
| `site/tests/unit/HashTabSync.test.tsx:20-26` | Fixture builds a `<starlight-tabs>` element that the shim never renders. See U1. |
| `site/tests/unit/build-renders.test.ts:119-135` | Title says "renders Starlight tabs". The `not.toContain('starlight-tab-item')` assertion is still a valid raw-marker guard, but the test returns early because `a1/weather` is no longer published, so it asserts nothing today. |
| `tests/workflow/scenarios/b2-hist-m41-full-pipeline.md:138`, `tests/workflow/specs/b2-hist-m41-full-pipeline.yaml:44` | Expected output `docusaurus/docs/hist/…`. |
| `scripts/debug/debug_module_json.js:5`, `scripts/legacy/typescript/generate-mdx.ts`, `scripts/assets/scripts-deprecated/README.md` | Docusaurus-era legacy code, already in `legacy`/`deprecated` trees. Archive-or-delete decision belongs to #5540, not here. |

### Class 1 — stale current documentation

| Reference | What is wrong |
| --- | --- |
| `site/README.md` | Title "Starlight Frontend", "built with Astro Starlight", `starlight/` tree, "Run from `starlight/`", `astro.config.mjs # Starlight + integrations`, `v6_build.py`. The most misleading file: it sits next to the truth anchors. |
| `site/plugins/README.md:1,5,11,17` | "Starlight Plugins", `starlight/src/data/…` paths. |
| `README.md:83-84,104,131,182` · `CONTRIBUTING.md:30,46,176` | "Astro Starlight", `cd starlight && npm install` (fails in a fresh clone). |
| `LICENSE-CONTENT.md:38,44` | Licence scope is defined by `starlight/src/…` globs that match nothing. Path-only fix; needs operator sign-off because it is a licence file. |
| `docs/SCRIPTS.md:565,576,581,939,1177,1181,1227,1240-1241` | Includes "Alias: `starlight`" for `services.sh`; `services.sh` contains no such alias (0 matches). |
| `docs/architecture/`: `ARCHITECTURE.md:54`, `system-topology.md:62,110-111,134,198`, `codebase-diagram.md` (8) + `.html` (9), `v7-pipeline.md:414,425,466`, `module-archetype-contract.md:57,65`, `agent-coordination-ledger.md:92-93` | Path and stack names. |
| `docs/best-practices/`: `git-hygiene.md:82`, `gitflow.md:144`, `lesson-schema.md:5`, `track-architecture.md:109` (+ `.html`), `word-atlas-design.md:210`, `writer-prompt-appendix.md:7,46`, `dual-mode-design-tokens.md:31`, `pipeline/v7-build-preservation.md` (7) | Path and stack names. |
| `docs/agents/AGENT-CAPABILITY-MATRIX.md:240,305`, `docs/agent-channels/pipeline/context.md:26`, `docs/epics/a1-upgrade-landing-contract.md:290-291`, `docs/folk-epic/EXEMPLAR-STANDARD.md:52`, `docs/folk-epic/folk-text-layer-spec.md:43` | "Starlight-native admonitions" etc.; admonitions come from `site/plugins/remark-admonitions.mjs`. |
| `docs/lesson-contract.md:28,77,117,122,203` · `docs/north-star.md:316` | **Prompt-injected**: loaded by `scripts/build/prompt_builder.py:9-10`; the committed `llm-qg-*-prompt.md` snapshots (class 2) contain these exact lines. Separate batch (D3) because the edit changes model-facing text. |

### Class 2 — historical evidence (do not rewrite)

- `docs/session-state/` (86 files), `docs/dispatch-briefs/` (43), `docs/handoffs/`
  (9), `docs/archive/`, `reviews/2026-05-10/`, `archive/`.
- Dated records: `docs/research/2026-06-12-*` (5) and
  `docs/research/lexicon/kaikki-fillability-2026-06-12.md`, `docs/plans/*` (4 named
  plans), `docs/decisions/*` (2), `docs/evidence/`, `docs/reports/`,
  `docs/bug-autopsies/node-modules-eloop-symlink.md`,
  `docs/monitor-api-ui-audit-2026-06-07.md`, `docs/salvage-manifest.md`,
  `docs/phase-4-exemplar-report.md`, `docs/reboot/`,
  `docs/architecture/2026-04-21-*`, `2026-04-22-*`, `v6-pipeline-review.{md,html}`.
- ADRs are permanent: `adr-003` and `adr-008` (Deferred) keep their `starlight/`
  paths. Supersede, never edit.
- All 19 `docs/` Docusaurus files are pre-Astro records (`docs/archive/`,
  `docs/dev/`, `docs/issues/`, `docs/proposals/`, `docs/l2-uk-en/MODULE-*`,
  `docs/resources/ukrainianlessons/`), plus
  `agents_extensions/shared/_archive/commands/module-stage-4.md` and
  `archive/tasks/`. Whether `docs/dev/` and `docs/issues/` move under an archive
  tree is a #5539/#5540 lifecycle question.
- Generated evidence, never hand-edited:
  `curriculum/l2-uk-en/a1/{things-have-gender,what-is-it-like}/**/llm-qg-*-prompt.md`
  (40 files × 6 lines — frozen snapshots of `docs/north-star.md` +
  `docs/lesson-contract.md`; they clear on the next QG run after D3),
  `curriculum/…/promote_quality.json`, `audit/**`, and
  `site/src/data/vesum-vocab-lemmas.json:5-12` (provenance block generated
  2026-05-21; `scripts/etymology/build_vesum_vocab_lemmas.py:19-21` already
  defaults to `site/…`, so a regeneration fixes it).
- Correct current usage, not residue: `adr-013`, `docs-authority-lifecycle.md`,
  `docs/plans/2026-09-17-docs-knowledge-rollout.md`,
  `2026-09-05-astro-7-vs-lighter-ssg.md`, `ui-template-matrix.md:123`,
  `ui-template-state-spec.md:19`,
  `docs/prompts/a2-certification-orchestration-prompt.md:63` — each names
  Starlight as retired.

### Class 7 — uncertain, bounded

| ID | Question | Evidence needed | Route |
| --- | --- | --- | --- |
| U1 | `HashTabSync.tsx:55` selects tabs via `panel.closest('starlight-tabs')`, and `:127` waits on `customElements.whenDefined('starlight-tabs')`. The shim renders `div.lu-tabs`, so that branch returns early. Does a deep link to an anchor inside a non-default tab still open the tab? | One Playwright check: load `/<lesson>/#<id-inside-tab-2>`, assert the panel is visible. | C3 |
| U2 | `docs/architecture/learner-runtime-and-build-split.md` is `status: DRAFT` (2026-05-31, pre-decision) and documents `./services.sh restart starlight`, which does not exist. Rewrite, or mark superseded? | Owner disposition; default is a `superseded` status plus a pointer, not a rewrite. | #5539 lifecycle |
| U3 | Are the `custom.css:249-282` rules that neutralise Starlight margins dead? | Check selector matches in built `dist/` HTML. | C4 |

## 4. Fix batches

Each batch is one PR with independent cross-family review. None is performed by
this report's PR.

**Docs-only**

- **D1 — contributor entry points:** `site/README.md`, `site/plugins/README.md`,
  `README.md`, `CONTRIBUTING.md`. `LICENSE-CONTENT.md` paths ride along only with
  operator sign-off.
- **D2 — curated reference docs:** `docs/SCRIPTS.md`, the `docs/architecture/`
  and `docs/best-practices/` rows of class 1, agent/epic/folk rows. Sequence
  after the #5539 IA decision if those files are about to move.
- **D3 — prompt-injected contracts:** `docs/lesson-contract.md`,
  `docs/north-star.md`. Treated as a prompt change: prompt review before merge.

**Code/test**

- **C1 — dead path configuration:** `.dagger` excludes (verify with a Dagger
  run that `site/node_modules` is no longer uploaded), `content_surface_gates.py`
  pattern (add a `site/src/` test case), `.trufflehogignore`, `pyproject.toml`
  excludes, `.yamllint`, `.gitignore` comments, `agents_extensions/shared/settings.json`
  (+ redeploy copies, + `docs/CLAUDE-CODE-FEATURES.md:78`).
- **C2 — cosmetic identifiers:** `site/package.json` name + lockfile,
  `starlightRoot`/`starlightNodeModules`, `STARLIGHT_*` constants with importers
  and the monkeypatch, root npm script names with their two callers, pytest
  marker text, test section headers. `module_archetypes.py` is excluded from C2
  and goes with D3 (prompt-visible).
- **C3 — tab deep-link behavior:** resolve U1; then rewrite or delete the
  `HashTabSync` branch and its fixture; re-point `build-renders.test.ts` at a
  published module so it asserts again.
- **C4 — CSS residue:** resolve U3; drop dead rules and stale comments.

## 5. Removal gate for the `@astrojs/starlight/components` alias

The alias and `site/src/starlight-compat/` stay until every predicate passes, in
order. This formalises the "Consequences" paragraph of the canonical record.

1. **Emitter:** `scripts/generate_mdx/core.py` emits the local path (for example
   `@site/src/starlight-compat`) and generator tests pin the new line.
2. **Regeneration:** a separately bounded PR regenerates or mechanically rewrites
   the committed importers (400 files at `1f7694e857`). Import-line-only diff;
   this is the >20-file move carve-out, never mixed with behavior changes.
3. **Zero importers:**
   `git grep -l '@astrojs/starlight/components' -- site/src/content scripts tests`
   returns nothing.
4. **Mirror:** `tests/build/upgrade_browser_check.mjs:38` drops its copy of the
   alias in the same PR as step 5.
5. **Removal:** delete the alias line; `npm run build` and `npm test` in `site/`
   are green, and the Pages size gate passes.

Renaming the `starlight-compat/` directory is optional and only after step 5.

## 6. Out of scope

No rename, no alias or shim change, no curriculum content, no historical
rewrites, nothing under `audit/` (owned by #5536), no OpenWiki.
