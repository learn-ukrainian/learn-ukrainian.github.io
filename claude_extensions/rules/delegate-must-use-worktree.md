# Delegated Work MUST Use Git Worktree

<critical>

When you dispatch work to Codex, Gemini, or any other agent via
`scripts/delegate.py dispatch` (or any equivalent), the agent MUST work
in a git worktree — **not** a feature branch in the main checkout.

## Why this matters

`critical-rules.md` says: *"All work on `main`. Use `git worktree` for
isolation."* If delegated work creates a feature branch inside the main
checkout directory (`git checkout -b ...`), it:

- Switches HEAD of the main checkout off `main`, silently
- Mixes delegated work with any uncommitted work the user has
- Breaks scripts that expect `main` to be current
- Violates the "all on main" convention

This happened on 2026-04-21. I wrote a Codex brief saying *"Commit as a
feature branch + single PR if possible"* without specifying WHERE.
Codex ran `git checkout -b feature/gemini-fallback-ladder` inside the
main checkout. Cleanup was awkward (user had running scripts, couldn't
switch HEAD). The rule exists so this never happens again.

## MANDATORY in every dispatch brief

Every Codex / Gemini dispatch prompt MUST include wording equivalent to:

```
## Worktree instructions (mandatory)

Work in a git worktree at `.worktrees/<task-name>`. Do NOT create a
feature branch in the main checkout. Concrete setup:

    git worktree add -b <task-branch-name> .worktrees/<task-name>
    cd .worktrees/<task-name>
    # do work, commit, push

The main checkout (wherever the user is working) stays untouched on
`main`. After the PR merges, the worktree is cleaned up by the user
or the next agent session:

    git worktree remove .worktrees/<task-name>
    git branch -d <task-branch-name>

If the work truly cannot be done in a worktree (extremely rare —
usually only repo-wide mass migrations), STOP and ask for approval
before creating any branch.
```

Use descriptive names: `codex-<issue-number>-<short-topic>`,
`gemini-<issue-number>-<topic>`. Not generic names like `feature/*`.

## Post-merge cleanup

When a worktree's PR merges to main, the worktree and its branch MUST be
deleted. This is NOT optional — stale worktrees accumulate and pollute
`git worktree list`.

Check with:

    git worktree list

Remove with:

    git worktree remove .worktrees/<name>
    git branch -d <branch>

## When YOU (not a delegated agent) need isolation

Same rule — use a worktree. Don't branch in the main checkout.

    git worktree add -b claude-<issue>-<topic> .worktrees/claude-<issue>-<topic>
    cd .worktrees/claude-<issue>-<topic>

## Enforcement

The rule lives in both `claude_extensions/rules/` (this file) and will
fire on every session start. If you dispatch without the worktree
instruction, you're violating a critical rule — reread it and rewrite
the brief.

</critical>
