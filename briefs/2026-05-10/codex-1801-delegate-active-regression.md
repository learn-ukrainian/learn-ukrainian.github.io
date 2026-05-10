# Codex brief — #1801 `/api/delegate/active` regression + status-or-fail --help

**Issue:** #1801. Read the full body for ACs and severity context: `gh issue view 1801`.
**Task ID:** `codex-1801-delegate-active`
**Mode:** `--mode danger --worktree`
**Base:** `origin/main`

## Worktree (mandatory)

```
git worktree add -b codex-1801-delegate-active .worktrees/codex-1801-delegate-active origin/main
cd .worktrees/codex-1801-delegate-active
```

## What to fix

Per #1801 — two issues, all ACs in the issue body:

1. **Regression**: `scripts/api/delegate_router.py:148-155` — drop the `task.get("alive")` clause for `spawning` tasks so `/api/delegate/active` matches `active_delegate_count()`. Pin behavior with a fixture that includes `status="spawning"` + `pid=None`. Verify `/api/orient`'s `active_count` and the active list disagree before fix and agree after.
2. **CLI help**: `scripts/delegate.py:1572-1582` — add `description=` (exit-code semantics: 0 running / 1 not-running-or-stale / 2 API unreachable) + `epilog=` example to the `status-or-fail` subparser per `.claude/rules/cli-help-standard.md`. ~5 LOC.

NITs (issues 3-6) — skip unless clearly trivial. Issue 6 (em-dash drift in MEMORY.md:27) — DO NOT touch MEMORY.md, that's a different change surface.

## #M-4 evidence requirements

Commit body must include:

- Raw output of `curl -s http://localhost:8765/api/delegate/active` and `curl -s http://localhost:8765/api/orient` BEFORE fix (to demonstrate the regression).
- Raw output of `pytest tests/api/ -k "delegate"` AFTER fix.
- Raw output of `.venv/bin/python scripts/delegate.py status-or-fail --help` AFTER fix.

## Pre-submit checklist (AGENTS.md:11-26)

- `.python-version` / `.yamllint` / `.markdownlint.json` unchanged
- No artifact files in diff
- No `sys.executable`, no `@pytest.mark.skip pass`, no weakened assertions
- < 20 files changed
- ruff clean

## Workflow

1. `git worktree add -b codex-1801-delegate-active .worktrees/codex-1801-delegate-active origin/main && cd $_`
2. Read #1801 body fully: `gh issue view 1801`
3. Implement fixes (2 changes + 1 test)
4. `.venv/bin/ruff check scripts/api/ scripts/delegate.py tests/`
5. `.venv/bin/pytest tests/api/ -k delegate -x`
6. Capture #M-4 evidence outputs
7. Commit (conventional: `fix(api): /api/delegate/active counts spawning tasks (#1801)`); commit body has the evidence blocks
8. Push, `gh pr create` (title = commit subject, body references #1801 and pastes evidence)
9. Do NOT auto-merge.
