# Dispatch brief — Issue #1933 /goal driver 4 improvements

**Agent**: cursor (composer-2.5)
**Mode**: danger
**Effort**: high
**Branch base**: `origin/main`
**Task ID**: `issue-1933-goal-driver-improvements-2026-05-25`

## Read first
- `gh issue view 1933` — has the 4-item prioritized wishlist + the 2026-05-14 incident background
- `claude_extensions/rules/goal-driven-runs.md` — full /goal grammar (CRITICAL — pinned by #1884)
- `claude_extensions/hooks/goal-driver-stop.sh` — Stop hook that maintains per-session watcher state
- Current state file shape: `.claude/goal-state/<session_id>.json`

## Verifiable claims preamble (#M-4)
- "GOAL_WAIT supported" → quote a test that emits `GOAL_WAIT signal=<id> reason="..."` and verifies the Stop hook does NOT increment `no_progress`
- "abort clears hook" → quote a test where `GOAL_ABORT` is emitted and the state file is deleted
- "M cap auto-sized" → quote a test of `scripts.goal_driver.size_cap` against fixture inputs
- ruff + pytest green per usual

## Background
The 4 items from the issue:
1. **`GOAL_WAIT signal=<watcher_id>` status** — terminal-but-not-final suspend that doesn't count as `no_progress`. Goes in the status-line grammar.
2. **Abort clears Stop-hook fingerprint** — when `GOAL_ABORT` is emitted, the Stop hook MUST delete `.claude/goal-state/<session_id>.json` so the next `/goal` doesn't resume the dead watcher.
3. **Auto-sized `M` cap** — `M = clamp(15, queue_depth * 2 + 5 + async_waits, 200)` per the formula in `goal-driven-runs.md`. Ship as `scripts.goal_driver.size_cap` CLI module.
4. **(item 4 — read issue for full spec)**

The full doc was already updated 2026-05-12 with the grammar (`claude_extensions/rules/goal-driven-runs.md`). This issue is the IMPLEMENTATION work — the rule doc describes the contract, this dispatch makes the code match.

## Steps

1. `git worktree add -B fix/issue-1933-goal-driver-improvements .worktrees/dispatch/cursor/issue-1933 origin/main && cd .worktrees/dispatch/cursor/issue-1933`
2. For each of the 4 items, read the issue body section + the rule doc, then implement:
   - GOAL_WAIT parser update in `claude_extensions/hooks/goal-driver-stop.sh` + matching `scripts/goal_driver/` Python helpers
   - Abort-clears-hook in the Stop hook script
   - `scripts/goal_driver/size_cap.py` CLI (`python -m scripts.goal_driver.size_cap --queue-depth N --async-waits M` returns auto-sized M)
   - Item 4 per issue body
3. Add tests in `tests/test_goal_driver_*.py` for each item.
4. `.venv/bin/python -m pytest tests/test_goal_driver_*.py -q`
5. `.venv/bin/ruff check scripts tests`
6. Commit: `feat(harness): /goal driver GOAL_WAIT + abort-clears-hook + auto-sized M cap (closes #1933)`
7. Push, open PR.

## Stop conditions
- Item 4 of the issue is ambiguous → STOP and ask in PR body comment.
- Stop-hook script edits would break existing /goal runs → STOP, propose backward-compat.
- Test coverage drops below 80% on the new files → add more tests before opening PR.

## Done criteria
PR URL + `gh pr checks` + raw pytest summary for each goal_driver test file + an example status-line emit per new feature in the PR body.
