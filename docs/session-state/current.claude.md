# Current - Claude Thread Handoff (2026-06-06, cleanup + A-migration session)

> Read `docs/session-state/current.md` (router) first, then this file.
> origin/main at handoff: `35cacd8bde` (FF first thing). Tech-debt cleanup session, user-directed.

## ⏳ FINALIZE FIRST: `a-slice2` → PR #2765 (A migration slice 2) — REVIEWED CLEAN, merging
Slice 2 finished cleanly (codex, PR #2765). **I reviewed the diff: PASS** — exactly 3 files
(new `scripts/build/prompt_literals.py` + `v6_build.py` + `plan_patch.py`), no scope creep, 7 defs
(5 regexes + 2 funcs) moved, v6_build re-imports all 7 (back-compat), `plan_patch.py` repointed.
CI was pending `Test (pytest)` at handoff; a watcher was armed to merge on green.
**On wake:** `gh pr view 2765 --json mergeStateStatus,statusCheckRollup`. If green/CLEAN:
`gh pr merge 2765 --squash --delete-branch`, then `git worktree remove --force
.worktrees/dispatch/codex/a-slice2`. If pytest failed: read the failure, fix in the worktree
(the diff is a pure move — a fail is likely a missed re-import name), re-verify, merge.

## ✅ DONE THIS SESSION

### #1863 Repo cleanup sprint — Phase 3 EXECUTED (user said "have them done")
7 of 9 categories CLOSED, 6 PRs merged:
- B #2748 (PR #2757) 2 dead imports · C #2749 (PR #2758) 7 docs V6→V7 · D #2750 (PR #2761) 41 `.bak` removed ·
  E #2751 (PR #2760) **78 session-state handoffs archived** · F #2752 / I #2754 / J #2755 = no-op (investigated).
- **Tool fixed twice:** #2746 (`.worktrees`/`archive` exclusion — was inflating the report 77%), #2756 (surface scan failures).
- Epic #1863 Phase-3 box checked; full outcome in epic body + comments.

### 2 categories RECLASSIFIED as deferred refactors (proven unsafe to delete — OPEN)
- **A #2747** — `v6_build`/v5 still imported by live code (Monitor API, V7 pipeline, research-preseed). Migration, not deletion. **Being actively migrated — see below.**
- **G #2753** — 63 of 85 "duplicate" files are LIVE back-compat shims (every zero-import shim is invoked by path; `generate_level_status` has 29 callers). 22 are legit per-package names. Zero safe deletes — rename refactor. DEFERRED.

### A migration (#2747) — driving it slice by slice
- ✅ **Slice 1 MERGED (#2764):** `PHASES`/`PHASE_LABELS` → new `scripts/build/phase_constants.py`; Monitor
  API (5 files) + 2 tests repointed; v6_build re-imports (identity preserved). 343 tests green.
- ⏳ **Slice 2 in-flight** (a-slice2, above): prompt-literal helpers → `prompt_literals.py`, decouple `plan_patch.py`.
- ▶ **NEXT — Slice 3:** extract `_post_process_content` (v6_build.py:6315, DEEP — assess coupling first; it
  may pull in many internals) → repoint `scripts/build/post_processors/_migrations.py:65`. After 2-3,
  **no live (non-test) code imports v6_build.**
- ⏸ **Slices 4-5 (CHECKPOINT before these — design call needed):** (4) ~15 test files import v6_build
  internals (`step_write`, `step_check`, `_parse_skeleton_sections`…) — keep as renamed tested library vs
  retire with build path? (5) migrate research-preseed (`assess_research_queue.py`, `preseed_runner.py`)
  off the `build_module_v5.py` subprocess, or keep v5 as the research builder. Full roadmap in #2747 comments.

## ⚠ GOTCHAS (hit this session)
- **index.lock races**: concurrent agents (folk-orchestrator + cursor active in THIS checkout) + pre-commit's
  stash step cause transient `.git[/worktrees/*]/index.lock`. If a commit fails on it: confirm no real git
  proc (`pgrep -fl git`), `rm -f` the stale lock, retry. Hit 3×.
- **guard-main-worktree hook blocks `git branch -D` in the main dir** — do worktree cleanup WITHOUT
  `git branch -D` (the `--delete-branch` on merge handles the remote; local refs linger harmlessly).
  Lingering local branch `claude/extract-phase-constants` (merged, harmless).
- **agy #2739 false-timeout is INTERMITTENT** — pass `--initial-response-timeout 600`; cleanup-E hit
  needs_finalize and I recovered it manually. agy `--model "Gemini 3.5 Flash (High)"`, trailer `X-Agent: gemini/<id>`.
- **Local main has folk-agent's unpushed commit** (`dc0e2c9517`-class) — do NOT push local main; merge PRs
  server-side via `gh`, operate via worktrees branched from origin/main.

## NOT TOUCHED (other lanes — awareness only)
PR #2763 (folk SSOT migration — folk agent), #2601 (B1 pilot draft, codex). Issue #2532 (B1 cleanup, codex).

## Restart
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main && git merge --ff-only origin/main && git rev-parse --short HEAD
cat batch_state/tasks/a-slice2.json   # FINALIZE a-slice2 first (see top)
curl -s http://localhost:8765/api/delegate/active
gh pr list --state open --json number,title,isDraft
```
