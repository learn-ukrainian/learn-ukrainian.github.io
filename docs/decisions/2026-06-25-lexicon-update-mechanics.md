# Lexicon / Word Atlas — update mechanics & cadence

> **Status:** proposal — captures how lexicon content updates TODAY (#M-4-traced from config) and
> proposes the cadence + the two gaps to close. The cadence redesign (Gap 1) needs a fleet + user
> decision before building. **Lane:** infra (claude-infra). **Date:** 2026-06-25.

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
**Options (needs user decision):**
- (a) **Self-hosted runner** with the DBs → the Monday cron actually grows + opens a gated PR. Most
  automated; needs a machine + the DBs maintained on it.
- (b) **Documented local cadence** — run `make atlas && atlas-grow` after each content batch / on a manual
  schedule; commit the resulting gated PR. Simplest; relies on a human remembering.
- (c) **Hybrid** — split the reconciler (lemmatization needs only VESUM, which could ship as a slim
  CI-friendly subset) onto CI to *detect* deltas + open a "lexicon is N words behind content" issue, while
  the heavy enrich stays local. Lowest-maintenance signal without a self-hosted runner.

### Gap 2 — the practice deck is NOT wired into the regen → it drifts (CLOSING THIS NOW)
`generate_practice_deck.py` (shipped #3795) is not in `make atlas` nor any freshness gate, so when the
manifest updates the deck (`site/public/lexicon/practice-*.json`) silently goes stale vs the Atlas.
**Fix:** (1) add the deck regen to `make atlas`; (2) a CI **deck-freshness gate** — the deck's
`deckVersion` already embeds `_manifest_fingerprint(entries)`, so CI (which hydrates the manifest for the
Frontend build) can recompute the fingerprint and fail if it ≠ the committed deck's `deckVersion`. This is
the load-bearing guard so the deck can't drift. (Pairs with #3796 — Release-asset hosting for the deck.)

## Proposed cadence (recommendation)
1. **On content milestones** (a batch of modules/readings shipped): local `make atlas` → auto-grow → gated
   PR → review + self-merge. This is the real "update lexicon content" trigger.
2. **On dictionary-source updates** (rare — a VESUM/ЕСУМ bump): local `make atlas` full regen.
3. **Every manifest change regenerates ALL derived artifacts including the deck** (Gap 2 fix) — enforced by
   freshness gates so nothing silently drifts.
4. **Weekly auto-grow** stays as the safety net once Gap 1 is resolved (runner or hybrid signal).

## Open backlog (the "rest of the lexicon stuff")
- **#3796** — migrate the committed ~2.9 MB practice deck → Release-asset hydration (before it churns).
- **#3449** — publish the open dataset: `export_open_dataset.py` exists + runs from the fresh manifest, but
  its output (`data/lexicon-dataset/`) is **not committed** → run + commit + PR (check it isn't gitignored).
- **#3450** — inflected-form dedupe → canonical "form of «lemma»" cards (filter drops them at consumers via
  `lexeme_filter`; the manifest-level canonicalization is the remaining piece).
- **#3406** — ~24 ЕСУМ entries carry OCR mojibake bibliographic text (careful: a prior dirty regen was
  discarded — fix the data, re-enrich only those entries).
- **#3675** — auto-grow P1–P3 shipped; Gap 1 above is the remaining "make it actually run" piece.
