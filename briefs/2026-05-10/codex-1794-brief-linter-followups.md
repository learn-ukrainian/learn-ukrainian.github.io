# Codex brief — #1794 brief linter follow-ups

**Issue:** #1794. Read full body for ACs: `gh issue view 1794`.
**Task ID:** `codex-1794-brief-linter`
**Mode:** `--mode danger --worktree`
**Base:** `origin/main`

## Worktree

```
git worktree add -b codex-1794-brief-linter .worktrees/codex-1794-brief-linter origin/main
cd .worktrees/codex-1794-brief-linter
```

## What to fix (per #1794 ACs 1-4)

1. `scripts/audit/lint_dispatch_brief.py:48` — `PYTHON_RE` only scans inside fenced blocks (use `fence_id is not None` guard). No more flagging backtick-inline prose mentions.
2. `scripts/audit/lint_dispatch_brief.py:42` — `_has_main_cd` detects shape (absolute path, no `.worktrees/` segment) instead of grepping for `learn-ukrainian` substring.
3. `scripts/audit/lint_dispatch_brief.py:104` — wrap `path.read_text(encoding="utf-8")` in try/except `UnicodeDecodeError` → emit informative error and exit 1 (not bare traceback). Apply same fix in `#1789`-related codepaths if it shares this read pattern (grep `read_text(encoding="utf-8")` in `scripts/audit/`).
4. `tests/audit/test_lint_dispatch_brief.py` — add 3 parametrized rows: (a) backtick-inline prose mention passes clean; (b) two `.venv/bin/python` calls in same fence with first preceded by `cd` and second >5 lines below — expected behavior pinned; (c) `.venv/bin/pytest` / `.venv/bin/ruff` not flagged.

AC 5: regression-check the existing brief corpus — `find briefs/ -name '*.md' -exec .venv/bin/python scripts/audit/lint_dispatch_brief.py {} \;` should still flag the legitimate violations (~69 in the original review run; if number drifts ±10%, that's fine — but zero would mean over-broadening).

## #M-4 evidence (commit body)

- Raw output of regression check on existing brief corpus (count of legitimate flags before+after).
- Raw output of `.venv/bin/pytest tests/audit/test_lint_dispatch_brief.py -v`.

## Pre-submit checklist (AGENTS.md:11-26) — applies.

## Workflow

1. Worktree setup → 2. Implement → 3. ruff → 4. pytest → 5. Capture evidence → 6. Commit `fix(audit): brief-linter prose FP + portability + utf-8 (#1794)` → 7. Push → 8. `gh pr create` → 9. No auto-merge.
