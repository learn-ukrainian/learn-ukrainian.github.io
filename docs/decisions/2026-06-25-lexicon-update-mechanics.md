# Lexicon / Word Atlas — update mechanics & cadence

> **Status:** ACCEPTED — captures how lexicon content updates TODAY (#M-4-traced from config) and
> records the cadence + the two gaps to close. **The user decided both open questions on 2026-06-25**
> (see "User decisions" below): all big derived artifacts → Release assets, and Gap 1 is resolved by
> publishing the DBs as Release assets so a hosted cron hydrates them at runtime. **Lane:** infra
> (claude-infra). **Date:** 2026-06-25.

## User decisions (2026-06-25) — both open questions resolved

- **Q1 — host all big derived artifacts as Release assets: CONFIRMED.** The manifest already is (#3659);
  the **practice deck (#3796)**, the **open dataset (#3449)**, AND the source DBs (`vesum.db`,
  `sources.db`) all move to Release assets + `git rm` the committed copies + hydrate at build/run time.
  Rationale: derived/large artifacts bloat git history on every regen (git can't delta-compress them);
  Release assets are the project's standard escape hatch.
- **Q2 — Gap 1 (serverless auto-grow): RESOLVED.** Publish `vesum.db` + `sources.db` as Release assets;
  the GitHub-hosted weekly `atlas-grow` cron downloads them at runtime → serverless grow, **no
  self-hosted runner**. (~1 GB weekly download — acceptable on Actions.) This supersedes options
  (a)/(b)/(c) below with a fourth path: **(d) hosted runner hydrates the DBs from Release assets.**

## Current tracker snapshot (2026-07-03)

Current static Atlas counts:

- Atlas manifest: 5,393 entries, including 336 `form_of` records.
- Public search/browse: 5,383 entries, 61 search shards, 31 browse shards.
- Daily Word: 300 entries.
- Practice deck: 4,484 lexemes and 22 reviewed A1 cloze items.
- Source-inventory seeds: 280 rows total: 80 textbook, 147 private
  teacher-lesson, 33 Ohoiko/ULP, and 20 curriculum sample rows.

Closed tracker leaves that should not be treated as active backlog:

- #3932 - shard search and browse before 25k entries.
- #3796 - practice deck Release-asset hydration.
- #3449 - open attributed dataset Release-asset export.
- #3450 - inflected-form dedupe to canonical `form_of` cards.

Merged recent delivery PRs:

- #4074 - sharded lexicon search index.
- #4075 - static lexicon API contract.
- #4083 - Tatoeba cloze attribution preservation.
- #4084 - third textbook source-decision ledger batch.

Open board:

- #3936 - tracker/reliability coordination.
- #4160 - private teacher-lesson vocabulary intake; use privacy-safe source
  labels in committed artifacts.
- #3933 - Ohoiko/ULP source-safe intake.
- #3934 - textbook/headword intake beyond the current 80-row seed.
- #3797 - reviewed cloze expansion beyond the current 22 A1 items.

Daily Word, Practice, and cloze remain separate admission decisions. Atlas
browse/search growth must not automatically move rows into those learner
surfaces.

## TL;DR — when does lexicon content update?

There is no single continuous pipeline; it is a 3-layer system, and the heavy layer is **manual + local**
because the dictionary DBs (`data/vesum.db` ~967 MB, `data/sources.db`) are gitignored and too big for CI.

| Layer | What | Trigger today | Where |
| --- | --- | --- | --- |
| **1. Manifest (SSOT)** | `lexicon-manifest.json` Release asset (5,393 entries in the current pointer) — the Atlas word data | **manual `make atlas`** when content/sources change | local only (needs the DBs) |
| **2. Auto-grow** | find NEW lemmas in modules/readings → enrich → gated PR (#3675) | cron **Mon 07:23** + `workflow_dispatch` | `atlas-grow.yml` — **no-op on hosted runners** |
| **3. Derived artifacts** | search-index, daily-pool, open-dataset | part of `make atlas` | local |

`make atlas` = `build_data_manifest → enrich_manifest → generate_search_index → export_open_dataset →
generate_daily_pool → verify_manifest`. The manifest is published as a **GitHub Release asset** (#3659)
with a committed pointer; the build hydrates it (`hydrate-manifest.mjs`). The "Atlas Manifest Freshness"
CI gate + `check_atlas_manifest_enrichment` guard staleness/thin-manifest.

At **site build time** (`npm run hydrate`) the derived artifacts are regenerated from the entry-model
SSOT rather than the flat manifest: `atlas:build-db` materializes `data/atlas.db`, then
`atlas:build-search` (`generate_search_index.py --db`) and `atlas:build-daily`
(`generate_daily_pool --db`) rebuild the search/browse and Word-of-the-Day artifacts straight from that
database (GH #4385). Both generators keep their legacy `--manifest` mode for the local `make atlas`
pass, which runs before the DB exists; the `--db` mode is admission-identical (same selection logic,
SSOT-sourced), so the two paths agree.

## The two gaps

### Gap 1 — the auto-grow cron is dormant (no-op on GitHub-hosted runners)

`atlas-grow.yml` needs `data/vesum.db` + `data/sources.db` on the runner; hosted runners don't have them,
so the weekly run skips with a `::notice::`. So **content→lexicon growth only happens via a local manual
run** (or a self-hosted runner). Net: the lexicon does not actually auto-update from new content today.
**RESOLVED (user, 2026-06-25) → option (d):** publish `vesum.db` + `sources.db` as Release assets; the
existing hosted `atlas-grow` cron downloads (hydrates) them at the start of the run, then grows + opens a
gated PR — no self-hosted runner. The options below are recorded for context but (d) is the chosen path.

- (a) **Self-hosted runner** with the DBs → the Monday cron actually grows + opens a gated PR. Most
  automated; needs a machine + the DBs maintained on it. *(Not chosen — a self-hosted machine is a
  maintenance liability the project wants to avoid.)*
- (b) **Documented local cadence** — run `make atlas && atlas-grow` after each content batch / on a manual
  schedule; commit the resulting gated PR. Simplest; relies on a human remembering. *(Not chosen — the
  user wants it automated, not human-memory-dependent.)*
- (c) **Hybrid** — split the reconciler (lemmatization needs only VESUM, which could ship as a slim
  CI-friendly subset) onto CI to *detect* deltas + open a "lexicon is N words behind content" issue, while
  the heavy enrich stays local. Lowest-maintenance signal without a self-hosted runner. *(Not chosen —
  (d) gives the full grow, not just a detection signal.)*

### Gap 2 — practice deck freshness after Release-asset hydration

`generate_practice_deck.py` (shipped #3795) is no longer a committed-shard
problem: #3796 moved the practice deck to Release-asset hydration, and the
current pointer records 4,484 lexemes plus 22 A1 cloze items across the
per-level deck files. The remaining guardrail is policy, not storage: Daily
Word, Practice, and cloze admission must stay explicit and reviewed, especially
for source-inventory rows promoted to browse/search.

## Proposed cadence (recommendation)

1. **On content milestones** (a batch of modules/readings shipped): local `make atlas` → auto-grow → gated
   PR → review + self-merge. This is the real "update lexicon content" trigger.
2. **On dictionary-source updates** (rare — a VESUM/ЕСУМ bump): local `make atlas` full regen.
3. **Every manifest change regenerates ALL derived artifacts including the deck** (Gap 2 fix) — enforced by
   freshness gates so nothing silently drifts.
4. **Weekly auto-grow** becomes the live safety net once option (d) lands — the hosted cron hydrates the
   DBs from Release assets, grows, and opens a gated PR.

## Resolved backlog moved out of active work

- **#3796** — practice deck Release-asset hydration is closed. The current
  pointer is `site/src/data/lexicon-practice-deck.pointer.json`.
- **#3449** — the open attributed dataset is closed and pinned as the
  `atlas-open-dataset` Release asset. The current pointer is
  `data/lexicon-dataset.pointer.json`.
- **#3450** — inflected-form dedupe is closed; manifest entries now include
  canonical `form_of` cards instead of publishing those rows as ordinary
  article pages.
- **#3406** — targeted ЕСУМ OCR/mojibake cleanup is closed.
- **#3675** — stateless content/doc-import Atlas growth is closed. The Gap 1
  release-asset mechanics remain documented here as decision history, not as
  an active #3675 issue leaf.

## Current sequencing

1. Keep #3936 accurate as the delivery board; update it when leaves close.
2. Continue #4160 before more broad textbook/Ohoiko growth, using
   privacy-safe committed labels and neutral source locators.
3. Continue #3933 with source-safe Ohoiko/ULP rows only.
4. Continue #3934 with reviewed textbook/headword rows beyond the current
   80-row seed.
5. Continue #3797 for reviewed cloze expansion and Tatoeba go-live policy.
6. Admit rows to Daily Word, Practice, or cloze only through explicit
   `surface_admission` decisions.
