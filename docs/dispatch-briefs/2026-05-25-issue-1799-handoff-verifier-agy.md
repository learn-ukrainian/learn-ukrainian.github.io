# Dispatch brief — Issue #1799 handoff-verifier closed-world detection

**Agent**: agy
**Mode**: danger
**Effort**: medium
**Branch base**: `origin/main`
**Task ID**: `issue-1799-handoff-verifier-2026-05-25`

## Read first
- `gh issue view 1799` — has the full repro list of false negatives. Read end to end.
- Current state: `scripts/audit/lint_handoff.py` (or whatever name verifier landed under from #1792). `git grep -l "PATH_PATTERN" scripts/audit/` will locate it.

## Verifiable claims preamble (#M-4)
- "closed-world bug fixed" → quote running the verifier against each of the 4 false-negative repros from the issue body, all must now flag.
- "no regression" → quote existing tests passing.
- "ruff clean" + "pytest green" → final summary lines.

## Steps

1. `git worktree add -B fix/issue-1799-handoff-verifier-closed-world .worktrees/dispatch/agy/issue-1799 origin/main && cd .worktrees/dispatch/agy/issue-1799`
2. Replace the hardcoded `PATH_PATTERN` alternation with an **open-world regex** that matches the SHAPE of a referenced path/env-var, not a fixed list. Per the issue body, the shape is roughly:
   - `~/.<name>` (dotfile under home)
   - `.env[.<suffix>]` (env files)
   - Anything matching `[A-Za-z0-9._/-]+` adjacent to `cat|head|tail|less|source|export` keywords
3. Add a regression test asserting all 4 false-negative repros (`~/.bash_secret`, `~/.totally_not_a_real_file_xyz`, `.env.foofake`, `.env.foofake.production`) now flag.
4. `.venv/bin/python -m pytest tests/test_lint_handoff.py -q` (or whatever the test file is named — discover via `git grep`)
5. `.venv/bin/ruff check scripts tests`
6. Commit: `fix(audit): handoff-verifier open-world path detection (closes #1799)`
7. Push, open PR.

## Stop conditions
- The replacement regex would over-flag legitimate references (e.g. paths inside code blocks). If so, add a backtick/codefence guard before opening the PR.
- The verifier file's current shape doesn't match the issue body's description of `PATH_PATTERN` — verify by reading the file first, then update the brief in the PR body.

## Done criteria
PR URL + `gh pr checks` + raw verification quotes for all 4 repros.
