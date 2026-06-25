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

## TL;DR — when does lexicon content update?

There is no single continuous pipeline; it is a 3-layer system, and the heavy layer is **manual + local**
because the dictionary DBs (`data/vesum.db` ~967 MB, `data/sources.db`) are gitignored and too big for CI.

| Layer | What | Trigger today | Where |
|---|---|---|---|
| **1. Manifest (SSOT)** | `lexicon-manifest.json` (4575 entries) — the Atlas word data | **manual `make atlas`** when content/sources change | local only (needs the DBs) |
| **2. Auto-grow** | find NEW lemmas in modules/readings → enrich → gated PR (#3675) | cron **Mon 07:23** + `workflow_dispatch` | `atlas-grow.yml` — **no-op on hosted runners** |
| **3. Derived artifacts** | search-index, daily-pool, open-dataset | part of `make atlas` | local |

`make atlas` = `build_data_manifest → enrich_manifest → generate_search_index → export_open_dataset →
generate_daily_pool → verify_manifest`. The manifest is published as a **GitHub Release asset** (#3659)
with a committed pointer; the build hydrates it (`hydrate-manifest.mjs`). The "Atlas Manifest Freshness"
CI gate + `check_atlas_manifest_enrichment` guard staleness/thin-manifest.

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

### Gap 2 — the practice deck is NOT wired into the regen → it drifts (open; sequence after #3796)
`generate_practice_deck.py` (shipped #3795) is not in `make atlas` nor any freshness gate, so when the
manifest updates the deck (`site/public/lexicon/practice-*.json`) silently goes stale vs the Atlas.
**Fix:** (1) add the deck regen to `make atlas`; (2) a CI **deck-freshness gate** — the deck's
`deckVersion` already embeds `_manifest_fingerprint(entries)`, so CI (which hydrates the manifest for the
Frontend build) can recompute the fingerprint and fail if it ≠ the committed deck's `deckVersion`. This is
the load-bearing guard so the deck can't drift. **Sequence after #3796**: the freshness check differs for a
committed deck vs a Release-asset-hydrated deck, so build it once the deck-hosting decision lands.

## Proposed cadence (recommendation)
1. **On content milestones** (a batch of modules/readings shipped): local `make atlas` → auto-grow → gated
   PR → review + self-merge. This is the real "update lexicon content" trigger.
2. **On dictionary-source updates** (rare — a VESUM/ЕСУМ bump): local `make atlas` full regen.
3. **Every manifest change regenerates ALL derived artifacts including the deck** (Gap 2 fix) — enforced by
   freshness gates so nothing silently drifts.
4. **Weekly auto-grow** becomes the live safety net once option (d) lands — the hosted cron hydrates the
   DBs from Release assets, grows, and opens a gated PR.

## Open backlog (the "rest of the lexicon stuff")
- **#3796** — migrate the committed ~2.9 MB practice deck → Release-asset hydration (before it churns).
- **#3449** — open dataset is **already published in git** (`data/lexicon-dataset/`, 36 files / 1.6 MB,
  committed in #3633). BUT re-running `export_open_dataset.py` on today's manifest produces **31 MB** (the
  enrichment grew since #3633) — so the committed-dataset approach **bloats on every regen**. This is the
  same derived-artifact-hosting problem as the manifest (#3659) and the deck (#3796): **migrate the dataset
  to a Release asset** (and `git rm` the committed copy) so regen doesn't grow git history.
- **#3450** — inflected-form dedupe → canonical "form of «lemma»" cards (filter drops them at consumers via
  `lexeme_filter`; the manifest-level canonicalization is the remaining piece).
- **#3406** — ~24 ЕСУМ entries carry OCR mojibake bibliographic text (careful: a prior dirty regen was
  discarded — fix the data, re-enrich only those entries).
- **#3675** — auto-grow P1–P3 shipped; Gap 1 above is the remaining "make it actually run" piece, now
  unblocked by the option-(d) decision (publish the DBs as Release assets → hosted cron hydrates them).

## Sequencing (the order the Release-asset migrations land)
1. **#3796 — practice deck → Release asset** (named-first, "before it churns"; establishes the
   deck-hydration pattern these others reuse).
2. **DBs (`vesum.db`, `sources.db`) → Release assets + atlas-grow cron hydration** (Gap 1 / #3675-(d)).
3. **#3449 — open dataset → Release asset** (`git rm` the committed 1.6 MB copy that re-exports to 31 MB).
4. **Gap 2 — deck-freshness gate** (after #3796, once the deck is hydrated, so the freshness check targets
   the pointer rather than committed shards).
