# Current — Claude Session Handoff (2026-06-19 — queue grind: 7 merged, 3 closed, lexicon bugs fixed)

> **ROLE:** main orchestrator (standalone session). Cold-started, ground the queue end-to-end:
> reviewed/merged the gemini batch + my own PRs, root-caused the two failing lexicon PRs and drove
> fixes via codex, kept Atlas honest. Quality non-negotiable; used the fleet (#M-12), self-merged on
> review + CI-green, didn't idle.

## STARTUP (repeats — do this)
Local main cold-started **28 behind origin** with a half-staged **#3601 system-file contamination**
(`agents_extensions/shared/hooks/heal-core-bare.py`, `scripts/core_bare_watchdog.sh`, `settings.json` +5)
in the index + stale lexicon artifacts. Resolved via `git reset --hard origin/main` (dirty-startup
protocol). #3601's work is safe on its PR branch. If you see that staged contamination again, reset is
correct — it reverts an *unauthorized* local system change, not making one.

## ✅ MERGED THIS SESSION (7)
- **#3624** (mine, #M-13) — UA admonition + nav labels + un-hide folk nav. Root-cause: removed the `isB1`
  English-leak gate (was leaking English nav for folk/seminars/core). UA labels verified correct.
- **#3595** — chtyvo→diasporiana dead-link (#3175). Replacement URL verified resolving to the exact book.
- **#3604** — bio↔lit audit heuristics (alias table + thematic filter). Inline-reviewed; bio-track tooling
  (recorded for bio-driver awareness).
- **#3603** — calque cross-feed (#3098): 5 phrasal calques linguistically verified + well-sourced;
  `_reverse_calques()` + Astro renderer clean.
- **#3629** (mine) — Atlas fingerprint refresh follow-up to #3603 (DB-free code-hash; #3626→#3628 pattern).
- **#3606** — docs API HTML-UI extensions (.css/.js/.woff/fonts) + ALLOWED_ROOTS key rename (#1814).
  Verified rename breaks NO consumer (comms.html ref = display text; discovery keeps backward-compat keys).
- **#3631** (supersedes #3598, form-of dedup #3450) — codex fix: rebased + resolved the
  build_data_manifest.py conflict with #3626's slug-fold, fixed coverage gate to **skip form_of records**
  (no double-count), 4 tests now genuinely assert the form_of card shape, Astro renderers updated,
  fingerprint refreshed. **Atlas verified on main: 4148 entries, 338 form_of cards, freshness OK, 33
  atlas tests pass.**

## ✅ CLOSED THIS SESSION (3)
- **#3605** (deps #2732) — superseded by #3623 + regressive (idna 3.18 already on main; would downgrade
  mando 0.8.2→0.7.1, remove marker-pdf/mpmath). Isolated `.dagger/uv.lock` idna 3.17→3.18 noted as a
  clean follow-up if wanted.
- **#3598** (form-of) — superseded by #3631.
- **#3596** (open-data #3449) — superseded by **#3633 (merged)**: scoped to ADDITIVE publication. #3633
  ships `data/lexicon-dataset/` (ATTRIBUTION/NOTICE/README + sharded JSONL) + `export_open_dataset.py` +
  Makefile export, KEEPS the committed manifest, and DROPS the out-of-scope manifest-delete + gitignore +
  Node reconstitute restructure (which broke pytest — Node prebuild hooks don't run before pytest).
  **De-bloat alternative (reconstitute-from-dataset model) is a SEPARATE deliberate decision for the
  user — not auto-adopted.**

## ⏭️ OPEN / NEXT
- **#3601** (core.bare watchdog #2842) — **HELD: needs USER GO** (hooks + settings.json; MIRROR FAILURE).
- **#3632** (folk URL gate #3162) — **folk-track-owned** (folk driver opened it this session). Awareness
  only; do NOT merge.
- **`make atlas` regen** (task #5) — committed manifest (4148) predates #3603's reverse_calques. A
  deliberate main-tree regen (DBs sources.db+vesum.db, ~33min, reaper-safe) syncs reverse_calques +
  confirms form_of/fold consistency + refresh fingerprint. Not bundled into a PR. Run when ready.

## ⚠️ INFRA OBSERVATIONS (for the user / next session)
- **`.agent/claude-thread-handoff.md` is shared between the main Claude orchestrator and the Claude folk
  driver** (same generic "claude" path). The folk driver overwrote it mid-session with its folk handoff.
  Cold-start SessionStart hook will feed the next session whichever wrote last — a cross-wire. THIS file
  (`docs/session-state/current.claude.md`) is the reliable main-orchestrator SSOT; read it, not the
  `.agent` file, when you are the main orchestrator. Proper fix (needs user go): per-role thread-handoff
  paths (e.g. `.agent/claude-main-handoff.md` vs `.agent/claude-folk-handoff.md`).
- **Stale worktrees** (pre-existing, NOT cleaned — folk-owned or uninvestigated, #M-10 forensics risk):
  `codex/atlas-cleanup`, `codex/b1-m83-reported-speech-certify`, `codex/fix-3600-shim`, `codex/fix-3600-sweep`,
  `codex/fix-pytest-push-hook-test`, `codex/folk-retest-kalendarna`, `cursor/deps-complete`,
  `gemini/2732-fix-dependencies`, `claude/folk-3632-fix`, `claude/folk-wikis-wave8`. Investigate + reap
  the merged/clean non-folk ones deliberately (don't mass-force).

## NOTES
- Only required CI on main = `Test (pytest)`. Atlas Freshness / Frontend / CodeQL = advisory.
- Atlas SSOT: `docs/atlas-data-coverage-strategy.md`. Verify-before-promote: #M-11. Fingerprint is
  DB-free (`scripts/lexicon/manifest_fingerprint.py` hashes `scripts/lexicon/*.py`); refresh after any
  lexicon-code change via `write_fingerprint()`.
