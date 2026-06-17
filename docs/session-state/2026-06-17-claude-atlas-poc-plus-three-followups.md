# Claude session handoff — Atlas finished (data+design) + 3 follow-ups dispatched (2026-06-17)

> **ROLE:** main orchestrator. User wants the Atlas FULLY done; defines "done" as the 3
> follow-ups below ALSO implemented. Drive them to merge; recover codex stalls yourself.

## ✅ SHIPPED + MERGED this session
- **#3393** immersion source sync (A2 full-immersion 85-100%; English never raised — user HARD rule, see MEMORY #M-13).
- **#3405** Atlas core data fills (kaikki direct: stress 98.2%, meaning 97.0%, etymology 81.7%) + **#3331 fixed** (deterministic wiki cache).
- **#3416** CEFR 65→99.9% (PULS preserved 0-overwrite + labelled GRAC estimates) + 29/29 proper-noun glosses.
- **#3437** **Word Atlas POC design implemented** (docs/poc/word-atlas/*) — word-atlas.css adopted, all 15 sections, WordAtlasArticle.astro (in `src/lexicon/`, NOT src/components — lesson-schema scan), 0 stubs. Browser-verified light+dark vs POC. **Already deployed** (deploy-pages.yml run on current main).
- Hygiene: closed #3367 (stanza/udtools broken), #3331 (fixed); cleaned merged worktrees.

## 🔧 OPEN — drive to merge (sequence: manifest-touching work ONE AT A TIME, #M-9)
1. **#3150 auto-expansion — DISPATCHED `atlas-3150-autoexpand` (codex, in-flight).** Vocab-aware CI freshness gate (current fingerprint is CODE-ONLY) + make-atlas recipe/hook so a released module's words auto-appear. Verify+merge when PR lands.
2. **#3450 inflected-form dedupe** — fold single-word forms → canonical `form_of:<lemma>` cards (URLs preserved, no dup enrichment, no stubs). A prior attempt ballooned 2447→2800; confirm forms TAGGED not duplicated. Touches build_data_manifest + manifest + astro.
3. **#3449 open dictionary dataset** — publish lexicon JSONs in git for community. **Owner decision 2026-06-17 (RECORDED in #3449): publish ALL + attribute every source ("tell it's theirs, won't claim it") + takedown-on-request; NO license-gating.** Build sharded JSON/JSONL + README + ATTRIBUTION.md + NOTICE.md(takedown contact). (Also fixes the 25MB single-manifest diff problem.)

## ⚠️ CODEX STALL PATTERN (hit 4× this session) — recovery recipe
Codex goes stdout-SILENT mid `make atlas` / `npm run build` and stalls before commit (esp. with --silence-timeout 0). Detect: worktree mtimes idle >12-15min + no commit. Recover: `delegate.py cancel <task>`, then run the build step yourself in the worktree (`make atlas PYTHON=<repo .venv>` or `npm run build --prefix site`), verify, commit, PR. Worked every time. Dispatch these with build pre-run if possible.

## VERIFY CHECKLISTS
- Data PRs: §8 conformance 0 violations (`verify_manifest.py`), idempotent re-enrich (hash match modulo generated_at), lexicon pytest, ruff, spot-check fills for garbage.
- Design/frontend PRs: `npm run build --prefix site` green; serve dist + browser-compare to POC (light+dark); 0 "Стаття-заготовка" stubs.
- Deploy: MANUAL (`gh workflow run deploy-pages.yml`); push-auto-deploy intentionally disabled. After merging atlas data/design changes, trigger a deploy.

## Atlas architecture (confirmed)
words in `site/src/data/lexicon-manifest.json` (25MB, 2447 entries) → `[lemma].astro` getStaticPaths → 1 static page/word (POC design). build:full = `astro build` (does NOT run make atlas — uses committed manifest). New vocab needs `make atlas` + commit + deploy.
