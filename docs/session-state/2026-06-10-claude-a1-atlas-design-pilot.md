# Claude orchestrator session handoff — 2026-06-10 (A1+Atlas design pilot, worktree reaper, live deploys)

> Read `docs/session-state/current.md` (router) first, then this. Long dense session:
> PR-queue drain → worktree disk cleanup → worktree-reaper shipped → live A1+Atlas rollout →
> A1 admonition + dev-server fixes → design-fidelity decisions (B + Goroh/Wiktionary) → A1 POC pilot fired.

## ⏳ ONE THING IN FLIGHT (resume here)
**`codex/a1-poc-lesson-pilot`** dispatch is RUNNING (fired ~00:28). Wakeup scheduled (was 00:53) to poll.
- It's **B-pilot Step A**: build the POC lesson component framework (`Dialogue`, `RuleBox` w/ м/ж/с gender colors, `ObserveBox`, `MythBox`, `SourceBox`) + port the full POC CSS into `starlight/src/css/custom.css` (blue/yellow identity, `.exercise` card frame + 30 activity badges) + styled core header + convert ONE module `things-have-gender.mdx` ("Речі мають рід" = the POC's own example) to the components. **LOCAL ONLY — no deploy, no writer-prompt change, other 54 modules untouched.**
- Brief: `docs/dispatch-briefs/2026-06-10-a1-poc-lesson-pilot.md`. Design spec: `docs/poc/poc-lesson-design.html`.
- **On land:** review PR (don't merge/deploy) → restart astro → load `/a1/things-have-gender/`, compare to `poc-lesson-design.html` → confirm `/a1/weather/` still renders (no regression) → **hand the local URL to the user for sign-off**. Only after sign-off → Step B (writer-prompt change + batch regen, verify-local-before-deploy).
- Also running (NOT mine, folk lane): `folk-text-layer` (codex). Awareness only.

## 🧭 DECISIONS LOCKED THIS SESSION (user)
1. **Design direction = B** (regenerate content to POC structure, NOT just CSS) — with the guardrail **"verify locally before rollout."** Applies to both A1 lessons (poc-lesson-design.html) AND Word Atlas (poc-word-atlas-design.html). De-risk: framework + 1 reference module → user sign-off → writer-prompt automation → batch regen → deploy nothing until confirmed.
2. **Etymology source = Горох (goroh.pp.ua/Етимологія, live scrape, already in `scripts/rag/source_query.py`) + Wiktionary (50K in RAG, "cleanest for common words").** NOT v2 ESUM (`data/processed/v2/esum_vol1.jsonl` — Ukrainian prose OK but **cognate forms OCR-garbled**: Ьагса=barca, уакшіт=vacuum). NOT the DjVu at resource.history.org.ua (it's a scan; re-OCR = same garbage). The old `esum_vol{1..6}.jsonl` + the 36K-page `etymology-manifest.json` are garbage to be torn down.

## ✅ DONE THIS SESSION (live + merged)
- **PR queue drain:** merged **#2880** (A1 landing beta→released); closed **#2850** (superseded by agents reorg); flagged **#2854** (folk scraper, DIRTY, track-owned — leave for folk lane).
- **#2842 core.bare canary was dormant** — running API predated the wiring; restarted API → `git_core_bare_ok:true` live + auto-healing. Documented gotchas on the issue.
- **Worktree disk cleanup** (user: `.worktrees` was 11GB): freed ~8.7G → ~4.6G. Removed merged/clean/pushed worktrees; verified the A1-M1 pilots + grok-hermes + b1-044 + cursor-quiz-gate + ulp-stress are ALL **superseded** (work already on main) → preserve-then-reaped (committed to local branches first, recoverable).
- **Worktree reaper SHIPPED — PR #2883 merged** (`scripts/orchestration/reap_worktrees.py`): fixes the accumulation root cause (kubedojo parallel — they auto-reap on merge; we only printed the command). Reap-on-merge + reap-on-success wired into v7_build + delegate.py. Dry-run default; `--apply`, `--preserve-then-reap`, `--prune-merged-branches`. Dogfooded.
- **#2884 filed (HIGH):** a no-`--worktree` folk build polluted MAIN (commit a2792 swept uncommitted files onto main, broke ff). Recovered (reset to origin); forensics on branch **`salvage/main-pollution-a2792`**. Fix = guard `_persist_build_artifacts` against committing in the primary checkout.
- **LIVE ROLLOUT:** user reported old a1/a2/b1 removed → deployed A1 (released, 55 modules) + Word Atlas (`/lexicon/`, 63 lemmas) live via `gh workflow run deploy-pages.yml`. Verified.
- **A1 "empty Словник/Зошит" — NOT a content bug.** Root cause: **`jsxDEV is not a function`** on the LOCAL dev server (stale Vite pre-bundle) → all React islands crash → empty tabs. Live site was fine (prod JSX transform). Fix: `rm -rf starlight/node_modules/.vite && ./services.sh restart astro`. (Hardened durably — see next.)
- **A1 `:::` admonitions rendering raw (all 55 modules) — FIXED + LIVE, PR #2887.** `remark-directive` + `remark-admonitions` plugin → `<aside class="admonition">` in both markdown+MDX pipelines; CSS for 6 types. Also hardened dev: removed extraneous `preact`, added `react/jsx-runtime`+`react/jsx-dev-runtime` to `optimizeDeps.include`. Deployed + verified live (`/a1/weather/`: 0 raw `:::`, 4 asides).

## 📋 TASKS (current.md task list 1–7)
1. ✅ A1 ::: admonitions (PR #2887)
2. ✅ dev-server jsxDEV hardening (PR #2887)
3. ✅ A1 audit (only systemic bugs were #1+#2; all 16 islands resolve, all modules have vocab+workbook content)
4. ⏳ Word Atlas etymology: source decided (Goroh/Wiktionary); **teardown of 36K OCR etymology surface pending**
5. ⏳ Word Atlas redesign to POC (B) — `poc-word-atlas-design.html`, 14 sections, teal/yellow
6. ⏳ Lexicon enrichment (#2882) — fill POC sections from source DBs (synonyms/idioms/literary/wikipedia/CEFR/heritage/translate)
7. 🔄 A1 lesson restyle to POC (B) — **pilot dispatched (in flight)**

## ▶ NEXT ACTIONS (in order)
1. **Land + verify the A1 POC pilot** (above) → user sign-off on the look.
2. **Word Atlas etymology teardown** (Task #4): delete `/etymology/[slug]`+`index.astro` routes, `vocab-etymology-link.mjs` + `etymology-lemma-index.mjs`, unwire `vocabEtymologyLinker` from `astro.config.mjs`, clean `vesum-vocab-lemmas.json` xref, delete 31MB `etymology-manifest.json`. The 63-lemma lexicon is INDEPENDENT (won't break). Sequence AFTER any A1 astro.config edits land (conflict avoidance).
3. **Word Atlas gloss "chunk" leak** (11 entries) + HTML entities (`&amp;`/`&lt;`) in `lexicon-manifest.json` — clean at the generator (`scripts/lexicon/enrich_manifest.py`).
4. After A1 pilot sign-off → **A1 Step B**: writer-prompt (`scripts/build/phases/linear-write.md`) emits POC components → batch regen → verify-local → deploy.
5. **Word Atlas redesign (B)** to poc-word-atlas-design.html + enrichment (Goroh/Wiktionary etymology).

## ⚠ GOTCHAS / STATE
- **Deploy = manual:** `gh workflow run deploy-pages.yml --ref main` (~2-3min, builds main, 38K pages incl. Word Atlas etymology routes). Pages serves the workflow artifact. NOT auto on push.
- **Local dev jsxDEV recurrence:** if islands go empty / `jsxDEV is not a function` → `rm -rf starlight/node_modules/.vite && ./services.sh restart astro`. (Durable fix shipped, but cache can still go stale on dep changes.)
- **Reaper is on main:** `.venv/bin/python scripts/orchestration/reap_worktrees.py --dry-run` (safe) / `--apply`. Use it to clean merged worktrees instead of manual removal.
- **`salvage/main-pollution-a2792`** = forensics of the a2792 main-pollution (keep until #2884 fixed).
- **Working tree uncommitted (local, harmless):** `start-claude.sh` (native-binary self-heal), 4 dispatch briefs in `docs/dispatch-briefs/` (records — commit or leave).
- **POC design files:** `docs/poc/poc-lesson-design.html` (A1 lessons, blue/yellow, full component CSS read this session), `poc-word-atlas-design.html` (Word Atlas, teal/yellow, 14 sections), `poc-folk-lesson-design.html`, `poc-lit-lesson-design.html`, `poc-site-design.html`.
- **V7 SSOT read this session:** `docs/best-practices/v7-design-and-corpus.md` (4-tab shape; P1 Tab3 canonical = "Вправи" not "Зошит" — discrepancy noted; activity placement 4-6 inline/6-9 workbook; verify-before-promote checklist; m20 revert cautionary tale).
- Open PRs awareness-only: **#2854** (folk DIRTY, track-owned), **#2601** (B1 draft).

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git merge --ff-only origin/main
curl -s http://localhost:8765/api/delegate/active           # is a1-poc-lesson-pilot done?
gh pr list --state open --json number,title,headRefName     # find its PR
./services.sh status                                         # astro :4321, api :8765
# verify pilot locally: rm -rf starlight/node_modules/.vite && ./services.sh restart astro
#   then load http://localhost:4321/a1/things-have-gender/  vs docs/poc/poc-lesson-design.html
```
