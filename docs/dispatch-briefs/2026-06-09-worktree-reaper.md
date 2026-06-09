# Dispatch brief — worktree reaper (port kubedojo's reap-on-merge)

## Why
`.worktrees/` hit 11GB because worktree removal is a **printed suggestion that
nobody executes**: `scripts/build/v7_build.py` (~line 415) and `scripts/delegate.py`
(~lines 778, 840) both `print("  git worktree remove ...")` after work completes —
they never run it. Across many agents × many days, ~465MB content-heavy checkouts
pile up.

Sister project **kubedojo** uses git worktrees the same way but stays at ~479MB
because `scripts/quality/auto_merge_nits.sh` reaps the worktree + branch the moment
a PR merges (it watches the dispatch JSONL: on `merged` → cleanup; on
`merge_held_nits` → merge then cleanup; idempotent via a `.seen` file). Its header
even records hitting our exact bug: *"v2 only handled merge_held_nits, which left 7
worktrees behind from the early happy-path merges."* We never built the watcher.

## Deliverable
A robust, TESTED reaper keyed on PR state (more durable than a tail-watcher that can
die), plus wiring so build/dispatch reap on success.

### #M-4 verifiable-claims preamble
Every claim in your final report MUST be tool-backed. Quote raw output, never "I
checked X":
- "tests pass" → `.venv/bin/python -m pytest tests/orchestration/test_reap_worktrees.py -q` final line raw.
- "ruff clean" → `.venv/bin/ruff check <files>` final line raw.
- "dry-run correct" → paste the actual `reap_worktrees.py --dry-run` output block.
- "commit landed" → `git log -1 --oneline` raw. "PR opened" → `gh pr view --json url` raw URL.

## Numbered steps
1. The dispatch runs in an auto-created worktree (`--worktree`). Confirm `pwd` is the
   worktree, not the main checkout, before editing.
2. Create `scripts/orchestration/reap_worktrees.py`:
   - Scans only worktrees UNDER `.worktrees/` (NEVER touch worktrees outside it, e.g.
     `~/.codex/worktrees/*` — list via `git worktree list --porcelain`, filter by path
     prefix = the repo's `.worktrees/`).
   - For each, resolve branch + PR state (`gh pr list --head <branch> --state all
     --json number,state`).
   - **REAP** (`git worktree remove --force`) when ANY:
     - PR `MERGED` and worktree clean → remove worktree; branch may be deleted too
       (merged) but do it via the worktree dir, NOT `git branch -D` in main (the
       `guard-branch-switch-in-main.py` hook BLOCKS `git branch -D` in the main
       worktree — call `git worktree remove` only; leave branch reaping to a separate
       opt-in `--prune-merged-branches` that runs `git branch -d` (lowercase, safe)).
     - PR `CLOSED` and clean → remove worktree, keep branch.
     - `build/*` branch, clean, age > `--build-age-hours` (default 6) → remove
       worktree, KEEP branch (artifacts = #M-10 forensics live on the branch).
     - clean AND branch == `origin/<branch>` (pushed; `git rev-list --left-right
       --count origin/<b>...HEAD` == `0\t0`) → remove worktree, keep branch.
   - **PRESERVE** (skip + report with reason) when the worktree has uncommitted
     changes — UNLESS `--preserve-then-reap`, which runs INSIDE the worktree
     `git add -A && git commit --no-verify -m "wip: preserve <branch> before reap
     [skip ci]"` (committing to the LOCAL branch = #M-10-compliant, fully
     recoverable via `git worktree add <path> <branch>`) THEN removes. Default OFF.
   - `--dry-run` is DEFAULT (print candidates + reasons, change nothing). `--apply`
     performs removals. `--json` for machine output.
   - Use `--no-verify` on any commit (avoids pre-commit, which intermittently flips
     `core.bare=true` — issue #2842).
3. Wire-in (smallest change that closes the leak):
   - `scripts/build/v7_build.py`: after `_persist_build_artifacts` succeeds, CALL the
     reap (remove worktree, keep branch) instead of only printing it. Gate behind a
     `--keep-worktree` opt-out so failures can still be inspected (reap on success only).
   - `scripts/delegate.py`: in the dispatch `finally`, when the worker exited cleanly
     AND opened/updated a PR (or pushed == origin), reap the worktree. Keep on
     dirty-exit / nonzero / timeout for diagnosis. Add `--keep-worktree` opt-out.
   - Do NOT build a long-running tail-watcher; the GC sweep + on-success reap is more
     robust. (Optionally note in the module docstring how to cron `reap_worktrees.py
     --apply` as a backstop.)
4. Tests — `tests/orchestration/test_reap_worktrees.py` (use tmp git repos +
   monkeypatched `gh`):
   - merged+clean → worktree removed; dirty → preserved (skipped) by default;
     `--preserve-then-reap` → committed-then-removed; `build/*` clean+aged → worktree
     gone, branch kept; pushed==origin clean → removed; external worktree path →
     UNTOUCHED; `--dry-run` → zero filesystem change. Assert the main checkout is
     never mutated.
5. `.venv/bin/ruff check scripts/orchestration/reap_worktrees.py tests/orchestration/test_reap_worktrees.py`
   and `.venv/bin/python -m pytest tests/orchestration/test_reap_worktrees.py -q`.
6. Commit (conventional + `X-Agent` trailer):
   `feat(orchestration): worktree reaper — reap-on-merge + build/dispatch reap-on-success [#2842-adjacent]`.
7. `git push -u origin <branch>`.
8. `gh pr create` — title + body describing the leak, the kubedojo parallel, and the
   reap/preserve safety matrix. **Do NOT merge** (no `--allow-merge`).

## Guardrails
- Reaper must be SAFE-BY-DEFAULT: `--dry-run` default, never deletes a branch in the
  main worktree (hook-blocked anyway), never touches non-`.worktrees/` paths, never
  reaps a dirty worktree without `--preserve-then-reap`.
- Do NOT add new functionality beyond the reaper + the two wire-in call sites + tests.
