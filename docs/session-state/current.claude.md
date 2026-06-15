# Current — Claude Session Handoff (2026-06-16 — Atlas: translations + dedup + CEFR + slovnyk)

> **ROLE:** main orchestrator (infra/tooling/integration/merge). **Atlas completion is the active user priority.** User wants RESULTS + blunt NEED/HAVE/BLOCKING + verify-on-real-data. Big multi-PR session; user steered closely (PULS trust, functional-form carve-out, "lemmas yes").

> **State:** main moving (merge-train active — Codex B1/B2/folk content PRs auto-merging; track-owned, awareness-only). core.bare=false. Live hooks: #M-0.5 admin-guard + #M-7 pytest-push. **#M-5 secret-guard FIXED+merged (#3240) but still DEACTIVATED** — see pending go.

## ✅ Shipped this session (merged)
- **#3240** secret-guard false-positive fix (verified on deployed hook, 28/28).
- **#3254** kaikki/Wiktionary translation fill — **+58 clean translations**, 0 garbage (gloss-quality layer in `build_kaikki_lookup.py`: `_clean_gloss`/`extract_glosses`/`_is_meta_clause`/`_is_grammatical_form` + `is_clean_lemma` affix guard).
- **#3256** slovnyk.me **429-friendly fetch + resumable mirror builder** (`scripts/lexicon/build_slovnyk_mirror.py`). **RESOLVED #3097** — Retry-After + exp backoff; `LEXICON_SLOVNYK_DELAY` 0.12→0.34. KEY finding: cache is ~full (2666/2667); cache-hit = 0.2ms/lemma; the residual enrich cost is ~32-min **deterministic CPU**, not slovnyk.
- **#3266** **dedup-to-lemma TRANCHE 1** — 273 VESUM inflection→lemma folds via committed static map `data/lexicon/vesum_inflection_aliases.json` (deterministic, CI-safe). Applied SURGICALLY to the committed manifest (2667→2394, §8-clean, no vocab drift). 0 wrong-sense (hand-audited). **6 functional forms kept standalone per user:** `дякую/прошу/може/будь/будьте/вітаю`.

## 🟢 In flight
- **#3276** (fixes #3270) — §8 gate accepts modern technical VESUM-gaps (`контрфактичний`/`морфонеміка`) in BOTH live+offline modes via new `_MODERN_TECHNICAL_LEMMAS` allowlist. 29 tests + live-heritage integration CLEAN. **CI running; merge on green (routine fix).**

## ✅ Decided + recorded
- **CEFR = PULS-only, NO estimation, leave uncovered blank** (user call). Doc: `docs/decisions/2026-06-15-cefr-puls-only-no-estimation.md`. PULS VALIDATED: 90%-within-±1-level vs our own curriculum (1239 words); spot-check sane A1→C1; PULS covers A1–B2 only (C1 233, C2 0). `_cefr` is already PULS-only → no code change. State Standard 2024 (№279) has NO per-word list (descriptors only); Synchak's published 5,891 = our PULS 5.9K.

## ⏭️ RESUME — completing lemma-keying (user wants full "lemmas")
1. **Merge #3276** (if not already) → unblocks vocab refresh.
2. **Vocab refresh** — full `make atlas` (now §8-clean with #3276; ~32-min CPU enrich, slovnyk cache full). Brings committed manifest from stale 2394 → ~2437 current vocab + dedup, enriches the ~43 new vocab words. Mechanical; large diff (generated artifact, verify via verify_manifest + entry counts).
3. **Dedup TRANCHE 2** — the remaining ~85 inflected forms NOT folded by #3266:
   - **48 create-page cases** (`вареники→вареник`, lemma not separately taught) — fold = CREATE the lemma page. A few are functional (imperatives `заходьте→заходити`, time-ordinals `восьма→восьмий`) → same keep-standalone review as the 6.
   - **33 ambiguous homographs** (`біле→[білий,біль]`, `гори→[гора,горіти]`) — need per-word human "which lemma?" call.
   - Mechanism: extend `generate_vesum_aliases.py` / the curated lists; needs re-enrich for the new pages.
4. **#3255 dmklinger gloss cleanup** — reuse `_clean_gloss` for dmklinger's colon-prefix `Alternative form of X: <trans>` (49 pre-existing garbage). Needs re-enrich.

## ⛔ PENDING USER PRESENT-TENSE GO (system change)
**Re-register fixed `guard-secret-print.py` into `agents_extensions/shared/settings.json` + `bash scripts/deploy_prompts.sh`** → re-activate #M-5. Verified clean (28/28). Recommendation: do it. Held: hooks/settings change needs explicit present-tense go (2026-06-14 rule).

## ⚠️ HARD LESSON (reinforced repeatedly this session)
**VERIFY OUTPUT ON REAL DATA — passing tests ≠ correct.** kaikki fill's green tests hid garbage (бабусю→"accusative singular"); caught only by printing rows. dedup's "drop misspellings" would've deleted 465 valid phrases — caught only by classifying the real data. Always print/classify the actual output.

## Atlas plan (SSOT: `docs/atlas-data-coverage-strategy.md`)
translation/meaning/stress/grammar → ~100% reachable; etymology ~80% max; CEFR capped at PULS A1–B2 (decided: blank beyond). kaikki = CC-BY-SA; slovnyk.me СУМ-20 fine attributed.

## Other open infra
- #2842 core.bare flip — `check_core_bare.py --fix` exists, not hook-wired. Recheck after worktree churn.
- #2882 Atlas populate umbrella.

Prior handoffs: `2026-06-15-claude-atlas-completion-hooks-handoff.md` (CEFR source links), and the earlier translation-fill version of this file (git history).
