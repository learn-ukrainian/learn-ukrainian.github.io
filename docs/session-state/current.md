# Current — multi-agent index (2026-04-28)

> **Repo state: CLEAN.** As of session close 2026-04-28, no active agent
> threads, no in-flight builds, working tree empty, HEAD = origin/main.
> The "multi-agent concurrent writes" warning that previous current.md
> versions carried no longer applies — this is now a single-thread
> baseline. If a future session forks parallel work again, restore the
> warning.

## Latest handoff (read this first)

| Thread | Latest handoff | Status |
|---|---|---|
| **Wiki cleanup + lit-* completion + hygiene flush** | **`docs/session-state/2026-04-28-wiki-cleanup-and-hygiene-flush.md`** | **Closed clean** |

## Predecessor chain (most-recent first)

| Thread | Handoff |
|---|---|
| EPIC #1577 reboot — Round 3.5 shipped, decision pending on user re-run | `2026-04-26-session-close.md` |
| Round 3.5 prompt-tighten shipped (#1603) — full detail | `2026-04-26-round-3.5-shipped.md` |
| Round 3 QG bugfixes shipped (#1599) | `2026-04-26-qg-bugfix-shipped.md` |
| Phase 4 round 3 dispatched (strict-JSON exemplar) | `2026-04-26-evening-handoff.md` |
| Autonomous orchestration during user-away window | `2026-04-26-autonomous-orchestration.md` |
| Overnight wiki rebuild + Phase 4 dispatch | `2026-04-26-overnight-claude.md` |
| EPIC #1577 reboot — Phase 0–3 done, Phase 4 staged | `2026-04-26-overnight-1586-phase4.md` |
| EPIC #1550 a1/1 verification (Unit 6 A/B) | `2026-04-25-orchestration-final-with-data.md` |
| Wiki retrieval overhaul (#1553) | `2026-04-25-wiki-retrieval-overhaul-1553.md` |
| Cold encode complete → next is #1569 | `2026-04-25-cold-encode-complete.md` |

## Cold-start protocol

1. Read this index.
2. Open `2026-04-28-wiki-cleanup-and-hygiene-flush.md` for the latest
   state and open questions.
3. If picking up a specific Phase-4 thread, also open the relevant
   predecessor (mostly `2026-04-26-round-3.5-shipped.md` for the round
   3.5 vs 4 decision).
4. If you create a new handoff, **add a row to the "Latest handoff"
   table above and shift the previous "Latest" into "Predecessor
   chain"** — do NOT replace this whole file.

## Cross-thread notes (still active)

- **Phase 4 round 3.5 SHIPPED** (`9294dedbbe`, #1603). **Decision
  pending:** did Gemini comply with the anti-meta-narration directives
  on a fresh A1/20 build? If yes → 3.5 is canonical, Phase 5 fan-out
  begins. If no → empirical bakeoff trigger for round 4 (claude-tools
  vs gemini-tools). See `2026-04-26-round-3.5-shipped.md` decision table.

- **Wiki rebuild fully landed.** All 8 lit-* tracks complete on main
  (435 articles), all other namespaces (academic, figures, folk,
  grammar, historiography, linguistics, mastery, pedagogy, periods)
  refreshed post-#1592 citation-shift. `wiki/.state/progress.db` has
  1492 articles, all post-shift, disk:DB sync clean.

- **Wiki search-index rebuild pending.** When the wiki rebuild
  finished (it has — see 2026-04-28 handoff), the search index needs
  refresh against the new artifacts. Also: `wiki/index.md` was last
  regenerated mid-rebuild and should be re-built via
  `.venv/bin/python scripts/wiki/compile.py --update-index`.

- **Cold-encode 88,192 units / 4 corpora committed 2026-04-25 evening**
  (wiki agent). All `up_to_date: true`. GDrive backup refreshed. The
  retrieval layer is consistent with PR #1555's paragraph-aware
  chunker.

- **Pyenv-rehash 60s lock — FIXED 2026-04-28.** Stale sentinel removed,
  preventive SessionStart hook now auto-cleans any sentinel >1 min old.
  See `claude_extensions/hooks/session-setup.sh` lines 6–32.

- **`~/.bash_secrets`** is where `GITHUB_TOKEN` lives. Not in any
  standard rc file. Source it manually before `gh` calls.

- **a1/1 working tree** (`.worktrees/verify-a1-1-phaseA-v5`) has
  user's preserved manual patches. Do NOT clobber.

- **Main is at `aae45828a0`** as of 2026-04-28 session close.
  Sequence of recent main commits worth knowing:
  - `aae45828a0` chore(hygiene): clean working tree
  - `192e5566d4` chore(wiki): complete lit-* rebuild
  - `01c59ae43e` fix(hooks): pyenv-rehash auto-clean
  - `1046b5a6e5` chore(wiki): include untracked rebuild artifacts
  - `b92d82b434` chore(wiki): rebuild snapshot + drop lit-doc/lit-crimea
  - `1be26297f0` docs(session): close addendum after round 3.5 (#1606)
  - `9294dedbbe` feat(phase-4): round 3.5 prompt + whitelist (#1603)
  - `a6b9e7f417` fix(phase-4): QG false-positive fixes (#1599)
  - `3603f11774` feat(phase-4): strict-JSON writer contract (#1598)

- **#1604 (open):** `PhraseTable` (and other vocabulary-tab activities)
  get `activity_type: null` in `lesson-schema.yaml`. Schema-generator
  fix needed. Not Phase-4-blocking.

- **`lit-doc` / `lit-crimea` scrub fan-out:** wiki/ tooling fully
  cleaned, but references remain in `scripts/api/`, `scripts/scoring/`,
  `scripts/generate_mdx/`, `scripts/build/v6_build.py`,
  `scripts/research/`, `scripts/tools/`, `scripts/sync/`. Filing as a
  separate issue is the recommended path. Not Phase-4-blocking.

- **Round-3 failed Gemini exemplar artifacts** preserved in repo
  `stash@{0}` and `stash@{1}` (duplicates). `git stash show -p
  stash@{0}` to inspect — useful for round 3.5 prompt-tightening
  evidence.

- **Adversarial review discipline** (added 2026-04-26 late): all 3
  agents (bot + Gemini + Codex) must review code PRs before merge.
  Drive-by bot is not a substitute. Reviews are cheap and parallel;
  silent merge then bug-then-fix is expensive.

- **CI bypass on chore-wiki pushes:** GitHub flags `Required status
  check "Test (pytest)" is expected` on direct main pushes. User
  account has bypass permission for `refs/heads/main`; pushes go
  through, audit log captures the bypass. Pytest still runs in CI
  background — check Actions tab if curious.
