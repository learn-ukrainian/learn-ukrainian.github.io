# Current — Claude Session Handoff (2026-06-16 overnight — #3277 atlas dedup-T2 SHIPPED · #M-5 reactivated · #2732 part1 done)

> **ROLE:** main orchestrator. User asleep, autonomous: "atlas top prio then infra, buried alive in issues, don't ask, finish it." Quality non-negotiable (#M-11).

> **State:** main = `590df3d782`+ (merge-train auto-merges Codex content/dependabot — awareness-only). Live hooks: **#M-5 secret-guard (reactivated this session)** + #M-0.5 admin + #M-7 pytest-push.

## ✅ SHIPPED this session (MERGED to main)
- **#3277 — Atlas dedup TRANCHE 2 (create-page folds).** T1(273)+T2(324, +51 create-cases) lemma-keying; manifest refreshed to **2436 entries**, §8 0 violations, all hazard scans CLEAN, freshness gate GREEN, Frontend build green.
  - **#M-11 REAL-DATA CATCH (the key event):** green gates HID a learner-visible bug — create-case lemma pages inherited the inflected *surface's* gloss/pos (`заходити` published `pos="imperative"`; `восьмий` masc. as «eighth (feminine)»). Renderer `[lemma].astro` shows gloss as subtitle+SEO and pos as a label. **Fixed** (`_atlas_record_for_manifest`: create-cases now null gloss/pos, keep enrichment.meaning, preserve surface in provenance; plain folds unchanged) + tests. Re-verified on real data before merge.
  - **Lesson reinforced:** §8/hazard/freshness gates passing ≠ correct. The freshness gate is **lexicon-CODE only** (not vocab — out of scope per #3150/#2928); always eyeball the real entries.
- **#M-5 secret-guard REACTIVATED** (`5837a1c09f`). Registered in PreToolUse[Bash], deployed to .claude/.codex/.agent, 37 tests, live-verified.
- **#2732 part 1 — lxml 6.1.0→6.0.4** (#3282 MERGED). The one genuine undocumented lock conflict (inscriptis hard-dep needs <6.1.0). CI green incl. pytest+pip-audit. Closed #3281 first (it chased the documented `requirements.txt:54-79` "DO NOT CHASE" pins — anthropic 0.97→0.46 etc.).

## 🟣 RESUME HERE (fresh session — context-handoff, heavy step deferred)
> This was a marathon session (#M-5 + #2732 + #3277 with 3 build cycles). I deferred the #3255 re-enrich to a fresh session for SHARP real-data verification (the #3277 bug was caught only because I was sharp). Do this first:

1. **#3255 dmklinger gloss cleanup — PR #3284 (DRAFT) CODE REVIEWED-APPROVED by me** (comment posted: reuse of `_clean_gloss` is correct + gated by `_is_meta_clause`, no fabrication, 96 tests pass). **Remaining = the re-enrich gate (orchestrator-owned):**
   - Branch `codex/dmklinger-gloss-3255`; PR changes `build_kaikki_lookup.py` + `enrich_manifest.py` → lexicon code changed → **freshness gate RED** until manifest+fingerprint regenerated.
   - Steps: `git worktree add .worktrees/claude/dmklinger-3255 codex/dmklinger-gloss-3255` (from origin); symlink DBs into the worktree (`ln -s /Users/krisztiankoos/projects/learn-ukrainian/data/sources.db <wt>/data/sources.db` + same for `vesum.db`); rebase on origin/main if behind; run `make -C <wt> atlas PYTHON=/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python` (~32-min warm-cache CPU; run_in_background, auto-wakes). VERIFY ON REAL DATA: pick a few dmklinger-sourced lemmas that had `Alternative form of X:` glosses and confirm they're now clean (gloss = the real translation, not the meta-prefix); §8 0 violations; freshness gate GREEN (`scripts/lexicon/check_manifest_freshness.py --root <wt> --fingerprint <wt>/site/src/data/lexicon-manifest.fingerprint.json` → exit 0). Commit manifest+fingerprint to the branch, flip #3284 ready, merge when CI green.
2. **#2732 follow-ups:** part 2 (.dagger/uv.lock idna — needs dagger SDK checked out); strategic #1634 (pip-freeze→real-resolver lock-gen + **isolate marker-pdf as an optional extra** so its caps don't gate the main lock) — architectural, needs a decision.
3. **Atlas remainder:** homograph curated pass (33 words, per-word judgment, NEVER auto-resolve — сьома/друга mis-merge is #1 fear); create-case **Богдан** minor (vocative-handler shadows the create-case → not created; pre-existing, not a #3277 regression; fix = vocative-vs-create precedence).
4. Triage remaining open issues. **#3153** telemetry + **#2738** VESUM-distractor decision = high blast/gate-scope, hold for interactive.

## ⛔ NEEDS USER (blocked on you)
- **#2036** hermes/anthropic logged out → run `hermes auth add anthropic` (OAuth) to restore the Claude-via-Hermes lane. Low urgency (native Claude dispatch lane available).

## Open worktrees / cleanup
- All session worktrees cleaned (dedup-t2, deps-lxml-2732, codex deps-lock-2732 removed). `.worktrees/builds/folk-koliadky-…` + codex dispatch worktrees remain (track-owned, awareness-only).

Atlas SSOT: `docs/atlas-data-coverage-strategy.md`. Prior handoff: `2026-06-15-claude-atlas-completion-hooks-handoff.md`.
