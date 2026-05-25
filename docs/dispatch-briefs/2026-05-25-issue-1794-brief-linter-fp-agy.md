# Dispatch brief — Issue #1794 brief-linter false-positive + hardcoded path

**Agent**: agy
**Mode**: danger (worktree + commits + push + PR)
**Effort**: medium
**Branch base**: `origin/main`
**Task ID**: `issue-1794-brief-linter-fp-2026-05-25`

## Read first
- `gh issue view 1794` — the full AC + repros are in the issue body. Read it end to end before editing.
- Current state of the linter: `scripts/audit/lint_dispatch_brief.py`.

## Verifiable claims preamble (#M-4)
Every claim in your final PR body MUST be backed by a quoted command + cwd + raw output:
- "false positive is fixed" → quote the linter run against a prose-mention test fixture (raw stdout)
- "hardcoded path removed" → quote `git diff` showing the substitution
- "tests pass" → quote `pytest tests/test_lint_dispatch_brief.py -q` final summary line
- "ruff clean" → quote `.venv/bin/ruff check scripts tests` final summary

## Steps (numbered, per AGENTS.md pre-submit checklist)

1. `git worktree add -B fix/issue-1794-brief-linter-fp .worktrees/dispatch/agy/issue-1794 origin/main && cd .worktrees/dispatch/agy/issue-1794`
2. Fix the two issues stated in the issue body:
   - **False positive on prose mention**: `PYTHON_RE` at `scripts/audit/lint_dispatch_brief.py:48` matches every occurrence of `.venv/bin/python`, including backtick-inline mentions in prose/tables. Narrow the match: only flag when the match is NOT inside backticks AND is the first token of a line/command (typical invocation context).
   - **Hardcoded `learn-ukrainian` path**: find the hardcoded project name and replace with a relative-to-repo-root resolution (e.g. derive from `git rev-parse --show-toplevel` or accept a `--project-root` flag).
3. Add a test fixture in `tests/test_lint_dispatch_brief.py` covering both regressions:
   - prose mention in backticks must NOT trigger
   - the linter must work in a directory NOT named `learn-ukrainian`
4. `.venv/bin/python -m pytest tests/test_lint_dispatch_brief.py -q` → must be all-green
5. `.venv/bin/ruff check scripts tests` → must be "All checks passed!"
6. Commit (conventional): `fix(audit): brief linter prose-mention false-positive + drop hardcoded learn-ukrainian path (closes #1794)`
7. `git push -u origin fix/issue-1794-brief-linter-fp`
8. `gh pr create` with the verification quotes per #M-4

## Stop conditions
Stop and report if:
- The fix requires touching more than `scripts/audit/lint_dispatch_brief.py` + its test file
- Existing tests break (would indicate prior false-positive was being relied on)
- The hardcoded path turns out to be load-bearing for a reason not mentioned in the issue

## Done criteria
Reply with: PR URL, `gh pr checks <N>` raw output, raw pytest summary, raw ruff summary. No `--admin`, no `--auto`.
