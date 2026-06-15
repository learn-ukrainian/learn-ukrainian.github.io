# Current — Claude Session Handoff (2026-06-16 — Atlas: translations + dedup T1+T2 + CEFR + slovnyk + §8)

> **ROLE:** main orchestrator (infra/tooling/integration/merge). **Atlas completion is the active user priority — specifically lemma-keying ("I would like lemmas… i want atlas fully done").** Huge multi-PR session; user steered closely (PULS trust → cross-check, functional-form carve-outs, "stop asking, finish it").

> **State:** main moving (merge-train active — Codex B1/B2/folk content PRs auto-merge; track-owned, awareness-only). core.bare=false. Live hooks: #M-0.5 admin-guard + #M-7 pytest-push. **#M-5 secret-guard FIXED+merged but DEACTIVATED** — pending go below.

## ✅ Shipped this session (MERGED)
- **#3240** secret-guard false-positive fix (verified on deployed hook 28/28).
- **#3254** kaikki/Wiktionary translation fill — **+58 clean translations** (gloss-quality layer `_clean_gloss`/`extract_glosses`/`_is_meta_clause`/`_is_grammatical_form` + `is_clean_lemma` affix guard, all in `build_kaikki_lookup.py`).
- **#3256** slovnyk.me **429-friendly fetch + resumable mirror builder** — RESOLVED #3097. Finding: cache ~full; cache-hit=0.2ms/lemma; residual enrich cost is ~32-min **deterministic CPU**, not slovnyk.
- **#3266** dedup **TRANCHE 1** — 273 inflection→lemma folds, committed static map `data/lexicon/vesum_inflection_aliases.json`, applied surgically (2667→2394, §8-clean). 6 functional forms standalone (дякую/прошу/може/будь/будьте/вітаю).
- **#3276** §8 gate accepts modern technical VESUM-gaps (контрфактичний/морфонеміка) in both modes — RESOLVED #3270. Unblocks full `make atlas`.

## 🟢 IN FLIGHT — the resume point
- **#3277 (DRAFT) — dedup TRANCHE 2.** Map 273→**324** (+51 create-cases). Create-cases fold + CREATE the lemma page (вареники→вареник, заходьте→заходити, восьма→восьмий, Богдане→Богдан). Homographs (33) NEVER auto-resolved (caught a mis-merge сьома→сім; #1-fear → all standalone, deferred). +3 politeness standalone. Code+map+tests done, 18 tests pass.
  - **⏭️ TO FINISH #3277 (next session):** in the worktree `.worktrees/claude/dedup-t2` (branch `claude/dedup-tranche2-2882`, DBs symlinked) run a full **`make atlas`** (build_data_manifest + enrich_manifest + verify_manifest; ~32-min CPU enrich; §8 now clean via #3276). This regenerates the manifest (current vocab + T1+T2 folds, ~2480 entries) + fingerprint. **VERIFY ON REAL DATA** (new lemma pages exist + enriched; §8 CLEAN; counts; spot-check вареник/восьмий pages). Commit manifest + fingerprint → flip #3277 to ready → merge. This ALSO does the vocab refresh (manifest was stale at 2394).

## ✅ Decided + recorded
- **CEFR = PULS-only, NO estimation, blank uncovered** (user). Doc: `docs/decisions/2026-06-15-cefr-puls-only-no-estimation.md`. PULS VALIDATED 90%-within-±1 vs our curriculum; covers A1–B2 only. `_cefr` already PULS-only → no code change.

## ⏭️ AFTER #3277 — remaining lemma-keying + Atlas
1. **Homograph curated pass (33 words)** — per-word "which lemma?" for `біле/гори/сині/друга/сьома/жив/їм/…` (list: regenerate map analysis or see this session's transcript). Add resolved ones to the map as a curated dict; leave genuinely-ambiguous standalone. Each is a judgment call — do NOT auto-resolve (mis-merge = #1 fear).
2. **#3255 dmklinger gloss cleanup** — reuse `_clean_gloss` for dmklinger's colon-prefix `Alternative form of X: <trans>` (49 pre-existing garbage). Needs a re-enrich (bundle with #3277's or after).

## ⛔ PENDING USER PRESENT-TENSE GO (system change)
**Re-register fixed `guard-secret-print.py` into `agents_extensions/shared/settings.json` + `bash scripts/deploy_prompts.sh`** → re-activate #M-5. Verified clean (28/28). Held: hooks/settings change needs explicit present-tense go (2026-06-14 rule).

## ⚠️ HARD LESSON (reinforced 3× this session)
**VERIFY OUTPUT ON REAL DATA — passing tests ≠ correct.** (1) kaikki green tests hid garbage (бабусю→"accusative singular"). (2) dedup "drop misspellings" would've deleted 465 valid phrases. (3) tranche-2 homograph "sole taught candidate" mis-merged сьома→сім — caught ONLY by diffing+eyeballing the regenerated map. Always print/classify the actual output before commit.

## Atlas plan (SSOT: `docs/atlas-data-coverage-strategy.md`)
translation/meaning/stress/grammar → ~100%; etymology ~80% max; CEFR capped at PULS A1–B2 (blank beyond, decided). kaikki=CC-BY-SA; slovnyk.me СУМ-20 fine attributed.

## Open worktrees / cleanup
- `.worktrees/claude/dedup-t2` — KEEP (branch `claude/dedup-tranche2-2882`, #3277 draft; has vesum.db+sources.db symlinks for the enrich). Remove after #3277 merges.
- #2842 core.bare flip — `check_core_bare.py --fix` exists, not hook-wired. Recheck after worktree churn.

Prior handoff: `2026-06-15-claude-atlas-completion-hooks-handoff.md` (CEFR source links). This file's earlier intra-session versions are in git history.
