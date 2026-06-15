# Current — Claude Session Handoff (2026-06-15, late — Atlas translation fill + secret-guard merge)

> **ROLE:** main orchestrator (infra/tooling/integration/merge). **Atlas completion is the active user priority.** User wants RESULTS + blunt NEED/HAVE/BLOCKING reporting + the fleet used (dispatch + VERIFY). This session shipped two merged PRs; next regen-heavy work is gated on #3097 (see below).

> **State:** main @ `b278664243`, tree clean, core.bare=false. 0 active dispatches (Codex folk-dossier dispatches run in their own worktrees — track-owned, awareness-only). Live hooks: #M-0.5 admin-guard + #M-7 pytest-push. **#M-5 secret-guard FIXED + merged (#3240) but still DEACTIVATED** — see pending go below.

## ✅ Shipped this session
- **PR #3240** (`fix #M-5 secret-guard false-positives`) — verified on the DEPLOYED hook (28/28 real-input cases: all false-positive repros ALLOW, all real-secret shapes BLOCK), squash-merged.
- **PR #3254** (`fill Atlas translation gap from kaikki/Wiktionary`) — **+58 CLEAN translations** (gap 889→831), 0 garbage, 112 tests, verify_manifest clean, merged → `b278664243`. Manifest fully re-enriched (wiki_reference 243→543 bonus).
- **#3255 filed** — pre-existing dmklinger translation garbage (`Alternative form of X: <trans>`, 49 entries), out-of-scope follow-up with proper colon-formatting solution scoped.
- **#3097 updated** — root-caused the 96-min enrich tax (see below).

## ⛔ PENDING USER PRESENT-TENSE GO (system change — NOT self-authorized per 2026-06-14 rule)
**Re-register the now-fixed `guard-secret-print.py` into `agents_extensions/shared/settings.json` PreToolUse[Bash] (timeout 5) → `bash scripts/deploy_prompts.sh` → live-smoke.** This re-activates #M-5 enforcement on the orchestrator's own tool surface. The fix is verified clean (28/28). Recommendation: do it. Held only because activating a hook on my own execution surface is a settings/hooks change needing an explicit present-tense go.

## ⏭️ RESUME (REORDERED — #3097 now gates the regen-heavy items)
1. **#3097 — mirror slovnyk.me locally (build-time).** **NEWLY GATING.** A full `make atlas` enrich is 96 min because slovnyk.me 429-rate-limits us → `_SlovnykTransientError` → not cached (`enrich_manifest._slovnyk_cache` ~L982 `continue` w/o `changed=True`) → ~1000 lemmas re-fetch every run, cache never converges (4222→4222). **Every manifest-regenerating Atlas item inherits this tax.** Build the local mirror BEFORE items 2-3. (PR #3254 sidestepped via a 3s surgical translation-only re-application — not general.)
2. **Dedup-to-lemma** (USER-APPROVED, biggest lever) — inflected forms (бабусю, білі, вуха — CONFIRMED present this session) + misspellings shouldn't be standalone Atlas entries. Machinery EXISTS in `build_data_manifest.py`: `VESUM_CANONICAL_HEADS`, `VOCATIVE_TO_NOMINATIVE`, `NON_ATLAS_LEMMA_KEYS` (curated lists) — item is to AUTOMATE via VESUM lemmatization (word→lemma; if word≠lemma and not independently a headword, alias to lemma page; drop misspellings). Changes entry set → needs full re-enrich → gated on #3097. >50 LOC → dispatch (codex) or dedicated inline session.
3. **CEFR** — State Standard 2024 (mova.gov.ua №279) IS the A1–C2 framework but likely descriptors-only. Fetch the standard .docx + Synchak eLex2025 corpus-profile paper for a per-word dataset (links in `2026-06-15-claude-atlas-completion-hooks-handoff.md`). Decision pending (user): estimate-from-frequency+label vs leave blank. Do NOT fabricate exact levels.
4. **#3255 dmklinger gloss cleanup** — also needs a re-enrich → gated on #3097.

## Atlas plan (SSOT: `docs/atlas-data-coverage-strategy.md`)
translation/meaning/stress/grammar → reachable ~100%; **etymology ~80% max, CEFR can't hit 100%** (no per-word source). kaikki = CC-BY-SA fully open; slovnyk.me СУМ-20 fine to use attributed (non-commercial ed project — #1667 is anti-scraping posture, not a copyright wall).

## ⚠️ HARD LESSON (reinforced this session — internalize)
**VERIFY OUTPUT ON REAL DATA before merge — passing tests ≠ correct.** The kaikki fill's unit tests were green, but printing real fills caught garbage: inflected-form entries (бабусю→"accusative singular") and compound meta-glosses. Three root-cause filter fixes (affix exclusion, clause-level meta filter, pure-grammatical-form filter) came ONLY from eyeballing actual output across 52K lemmas. Always print the rows.

## Gloss-quality layer (now in `build_kaikki_lookup.py` — reusable)
`_clean_gloss` / `extract_glosses` / `_is_meta_clause` / `_is_grammatical_form` + `is_clean_lemma` affix guard. The dmklinger path (#3255) should reuse a shared version (handle its colon-prefix convention).

## Other open infra
- #2842 core.bare flip — `check_core_bare.py --fix` exists, NOT wired into a hook (proper fix = PreToolUse/session hook to auto-heal). Recheck after worktree churn.
- #2882 Atlas populate umbrella.

Prior detailed handoff (superseded for resume order): `docs/session-state/2026-06-15-claude-atlas-completion-hooks-handoff.md` (still has CEFR source links + Atlas per-field plan).
